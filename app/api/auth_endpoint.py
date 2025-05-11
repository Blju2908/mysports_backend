from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.supabase import get_supabase_client
from app.db.session import get_session
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from pydantic import BaseModel, EmailStr
from sqlmodel import Session
import logging

router = APIRouter(tags=["auth"])

logger = logging.getLogger("auth")

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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")

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