from fastapi import APIRouter, Depends, HTTPException, status, Body, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.supabase import get_supabase_client
from app.db.session import get_session
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from pydantic import BaseModel, EmailStr
from sqlmodel import Session, select
import logging
import random
import string
from datetime import datetime, timedelta
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import get_config
import os
import httpx

router = APIRouter(tags=["auth"])

logger = logging.getLogger("auth")

# Hole die Konfiguration
settings = get_config()

# Mail configuration
mail_config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.MAIL_USE_CREDENTIALS,
    VALIDATE_CERTS=settings.MAIL_VALIDATE_CERTS,
    TEMPLATE_FOLDER=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates")
)

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    email: EmailStr
    id: str
    
class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: UserResponse

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str

class OtpRequest(BaseModel):
    email: EmailStr

class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str

# OTP model for database
class OtpModel(BaseModel):
    email: str
    otp: str
    created_at: datetime
    expires_at: datetime
    
# In-memory OTP store (replace with database in production)
otp_store = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")

async def send_otp_email(email: str, otp: str):
    message = MessageSchema(
        subject="Dein Einmalpasswort für MySports",
        recipients=[email],
        template_body={"otp": otp},
        subtype=MessageType.html
    )
    
    fm = FastMail(mail_config)
    await fm.send_message(message, template_name="otp_email.html")
    logger.info(f"OTP email sent to {email}")

def generate_otp(length=6):
    """Generate a numeric OTP of specified length."""
    return ''.join(random.choices(string.digits, k=length))

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_201_CREATED: {
            "model": UserResponse,
            "description": "User registered successfully.",
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Registration failed.",
        },
    },
)
async def register(user_data: UserRegister, db: Session = Depends(get_session)):
    """
    Register a new user with Supabase Auth. Returns only user info, no token.
    """
    logger.info(f"[Register] Attempting to register user: {user_data.email}")
    supabase = await get_supabase_client()
    try:
        response = await supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        # Supabase returns user=None if email is already registered
        if not response.user:
            logger.warning(f"[Register] Email already registered: {user_data.email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Diese E-Mail-Adresse wird bereits verwendet"
            )
        
        # Send confirmation email using Supabase's built-in functionality
        logger.info(f"[Register] User registered successfully, confirmation email sent: {response.user.email}")
    except Exception as e:
        logger.exception(f"[Register][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    try:
        user_model = UserModel(id=response.user.id)
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
        logger.info(f"[Register] User registered successfully: {response.user.email}")
        return UserResponse(
            email=response.user.email,
            id=response.user.id
        )
    except Exception as e:
        logger.exception(f"[Register][Exception] Error creating user model: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user record"
        )

async def _login(email: str, password: str) -> TokenResponse:
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_in_with_password({
        "email": email,
        "password": password
    })
    if not response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        user=UserResponse(
            email=response.user.email,
            id=response.user.id
        )
    )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    try:
        return await _login(login_data.email, login_data.password)
    except Exception as e:
        logger.exception(f"[Login][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        return await _login(form_data.username, form_data.password)
    except Exception as e:
        logger.exception(f"[Login-Form][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/request-otp", status_code=status.HTTP_200_OK)
async def request_otp(otp_request: OtpRequest):
    """
    Request an OTP for a new or existing user using Supabase's OTP functionality.
    This will send a "magic link" OTP email to the user regardless of whether they exist or not.
    """
    logger.info(f"[RequestOTP] Requesting OTP for: {otp_request.email}")
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_in_with_otp(
            {
                "email": otp_request.email,
            }
        )
        logger.info(f"[RequestOTP] OTP sent to: {otp_request.email}")
        return {"message": "OTP sent to your email"}
    except Exception as e:
        logger.exception(f"[RequestOTP][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    

@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(verify_request: OtpVerifyRequest, db: Session = Depends(get_session)):
    """Verify OTP and return session tokens for automatic login"""
    logger.info(f"[VerifyOTP] Verifying OTP for: {verify_request.email}")
    config = get_config()
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.verify_otp(
            {
                "email": verify_request.email,
                "token": verify_request.otp,
                "type": "email"
            }
        )

        # Handle the response from Supabase
        session = getattr(response, "session", None)
        user = getattr(session, "user", None) if session else None
        access_token = getattr(session, "access_token", None) if session else None
        refresh_token = getattr(session, "refresh_token", None) if session else None

        if not session or not user or not access_token or not refresh_token:
            logger.error(f"[VerifyOTP] Invalid response from Supabase: {response}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid OTP or session could not be created"
            )

        # Optionally, you could create the user in your own DB here if needed

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(email=user.email, id=user.id)
        )

    except Exception as e:
        logger.exception(f"[VerifyOTP][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OTP verification failed: {e}"
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    logger.info("[Logout] User logged out (token invalidated on client side only)")
    return {"message": "Successfully logged out"} 

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    logger.info(f"[Me] User info requested for: {current_user.email}")
    return current_user

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    try:
        supabase = await get_supabase_client()
        result = await supabase.auth.refresh_session(data.refresh_token)
        session = result.session
        if not session or not session.user:
            raise HTTPException(status_code=401, detail="Could not refresh token")
        return RefreshTokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=UserResponse(email=session.user.email, id=session.user.id)
        )
    except Exception as e:
        logger.exception(f"[Refresh][Exception] {e}")
        raise HTTPException(status_code=401, detail=f"Could not refresh token: {e}")

@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    supabase = await get_supabase_client()
    # Erst Passwort prüfen
    try:
        verify = await supabase.auth.sign_in_with_password({
            "email": current_user.email,
            "password": password_data.current_password
        })
        if not verify.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    # Passwort ändern
    try:
        update = await supabase.auth.update_user({"password": password_data.new_password}, token)
        if update.user:
            return {"message": "Password changed successfully"}
        raise Exception("Failed to change password")
    except Exception as e:
        logger.exception(f"[ChangePassword] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

@router.post("/change-email", status_code=status.HTTP_200_OK)
async def change_email(
    email_data: ChangeEmailRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme)
):
    supabase = await get_supabase_client()
    # Erst Passwort prüfen
    try:
        verify = await supabase.auth.sign_in_with_password({
            "email": current_user.email,
            "password": email_data.password
        })
        if not verify.user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password is incorrect"
            )
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is incorrect"
        )
    # E-Mail ändern
    try:
        update = await supabase.auth.update_user({"email": email_data.new_email}, token)
        if update.user:
            return {"message": "Email changed successfully. Please verify your new email address if required."}
        raise Exception("Failed to change email")
    except Exception as e:
        logger.exception(f"[ChangeEmail] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change email: {str(e)}"
        )