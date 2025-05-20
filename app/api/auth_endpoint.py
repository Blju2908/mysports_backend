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


class ChangeEmailRequest(BaseModel):
    new_email: EmailStr
    password: str


class OtpRequest(BaseModel):
    email: EmailStr
    check_user_exists: bool = False


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class SetPasswordRequest(BaseModel):
    password: str
    refresh_token: str
    current_password: str = None
    check_current_password: bool = False


# OTP model for database
class OtpModel(BaseModel):
    email: str
    otp: str
    created_at: datetime
    expires_at: datetime


# In-memory OTP store (replace with database in production)
otp_store = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")


async def _login(email: str, password: str) -> TokenResponse:
    supabase = await get_supabase_client()
    response = await supabase.auth.sign_in_with_password(
        {"email": email, "password": password}
    )
    if not response.user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(
        access_token=response.session.access_token,
        refresh_token=response.session.refresh_token,
        user=UserResponse(email=response.user.email, id=response.user.id),
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
        # First, check if the user exists by trying to get their profile
        supabase = await get_supabase_client()
        
        # Send the OTP
        response = await supabase.auth.sign_in_with_otp(
            {
                "email": otp_request.email,
            }
        )
        logger.info(f"[RequestOTP] OTP sent to: {otp_request.email}")
        return {"message": "OTP sent to your email"}
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"[RequestOTP][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    verify_request: OtpVerifyRequest, db: Session = Depends(get_session)
):
    """Verify OTP and return session tokens for automatic login"""
    logger.info(f"[VerifyOTP] Verifying OTP for: {verify_request.email}")
    config = get_config()
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.verify_otp(
            {
                "email": verify_request.email,
                "token": verify_request.otp,
                "type": "email",
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
                detail="Invalid OTP or session could not be created",
            )

        # Optionally, you could create the user in your own DB here if needed

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(email=user.email, id=user.id),
        )

    except Exception as e:
        logger.exception(f"[VerifyOTP][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OTP verification failed: {e}",
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
            user=UserResponse(email=session.user.email, id=session.user.id),
        )
    except Exception as e:
        logger.exception(f"[Refresh][Exception] {e}")
        raise HTTPException(status_code=401, detail=f"Could not refresh token: {e}")


@router.post("/set-password", response_model=TokenResponse)
async def set_password(
    password_data: SetPasswordRequest,
    current_user: User = Depends(get_current_user),
    token: str = Depends(oauth2_scheme),
):
    logger.info(f"[SetPassword] Setting password for user: {current_user.email}")
    try:
        supabase = await get_supabase_client()
        
        # Check current password if required
        if password_data.check_current_password:
            if not password_data.current_password:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is required",
                )
                
            try:
                verify = await supabase.auth.sign_in_with_password(
                    {"email": current_user.email, "password": password_data.current_password}
                )
                if not verify.user:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Current password is incorrect",
                    )
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Current password is incorrect",
                )
        
        # Set the session for the current user
        await supabase.auth.set_session(access_token=token, refresh_token=password_data.refresh_token)
        
        # Update user without passing token as separate argument
        update = await supabase.auth.update_user({"password": password_data.password})
        
        # Get new session/tokens
        user = await supabase.auth.get_user()
        session = await supabase.auth.get_session()
        
        if not session or not user:
            raise Exception("Failed to get new session after password update")
            
        return TokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=UserResponse(email=session.user.email, id=session.user.id),
        )
    except HTTPException:
        # Re-raise HTTP exceptions to preserve the status code
        raise
    except Exception as e:
        logger.exception(f"[SetPassword][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set password: {str(e)}",
        )
