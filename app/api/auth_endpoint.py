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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_session)):
    """
    Register a new user with Supabase Auth. Returns only user info, no token.
    """
    try:
        logger.info(f"[Register] Attempting to register user: {user_data.email}")
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        if not response.user:
            logger.error(f"[Register][Error] Supabase response: {response}")
            logger.error(f"[Register][Error] Supabase error: {getattr(response, 'error', None)}")
            logger.error(f"[Register][Error] Supabase user: {getattr(response, 'user', None)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        # Nach erfolgreicher Registrierung: UserModel-Eintrag anlegen
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
        logger.exception(f"[Register][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login with email and password (JSON body)."""
    try:
        logger.info(f"[Login] Attempting login for: {login_data.email}")
        supabase = await get_supabase_client()
        
        response = await supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        if not response.user:
            logger.warning(f"[Login][Error] Invalid credentials for: {login_data.email}")
            logger.debug(f"[Login][Error] Supabase response: {response}")
            logger.debug(f"[Login][Error] Supabase error: {getattr(response, 'error', None)}")
            logger.debug(f"[Login][Error] Supabase user: {getattr(response, 'user', None)}")
            logger.debug(f"[Login][Error] Supabase session: {getattr(response, 'session', None)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"[Login] Login successful for: {login_data.email}")
        return TokenResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user=UserResponse(
                email=response.user.email,
                id=response.user.id
            )
        )
    except Exception as e:
        logger.exception(f"[Login][Exception] {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password (form data)."""
    try:
        logger.info(f"[Login-Form] Attempting login for: {form_data.username}")
        supabase = await get_supabase_client()

        response = await supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        if not response.user:
            logger.warning(f"[Login-Form][Error] Invalid credentials for: {form_data.username}")
            logger.debug(f"[Login-Form][Error] Supabase response: {response}")
            logger.debug(f"[Login-Form][Error] Supabase error: {getattr(response, 'error', None)}")
            logger.debug(f"[Login-Form][Error] Supabase user: {getattr(response, 'user', None)}")
            logger.debug(f"[Login-Form][Error] Supabase session: {getattr(response, 'session', None)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        logger.info(f"[Login-Form] Login successful for: {form_data.username}")
        return TokenResponse(
            access_token=response.session.access_token,
            refresh_token=response.session.refresh_token,
            user=UserResponse(
                email=response.user.email,
                id=response.user.id
            )
        )
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
    """
    Refresh the access token using a refresh token.
    """
    try:
        logger.info(f"[Refresh] Attempting refresh for refresh_token: {data.refresh_token[:8]}... (truncated)")
        supabase = await get_supabase_client()
        session = await supabase.auth.refresh_session(data.refresh_token)
        if (
            not session
            or getattr(session, 'error', None)
            or getattr(session, 'access_token', None) is None
            or getattr(session, 'user', None) is None
        ):
            logger.warning(f"[Refresh][Error] Invalid session or missing attributes: {session}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        logger.info(f"[Refresh] Token refresh successful for user: {session.user.email}")
        return RefreshTokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=UserResponse(
                email=session.user.email,
                id=session.user.id
            )
        )
    except Exception as e:
        logger.exception(f"[Refresh][Exception] {e}")
        raise HTTPException(status_code=401, detail="Could not refresh token")