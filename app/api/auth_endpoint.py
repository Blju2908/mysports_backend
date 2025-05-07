from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from app.core.supabase import get_supabase_client
from app.db.session import get_session
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from pydantic import BaseModel, EmailStr
from sqlmodel import Session

router = APIRouter(tags=["auth"])

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
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        if not response.user:
            print(f"[Auth][Register][Error] Supabase response: {response}")
            print(f"[Auth][Register][Error] Supabase error: {getattr(response, 'error', None)}")
            print(f"[Auth][Register][Error] Supabase user: {getattr(response, 'user', None)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
        # Nach erfolgreicher Registrierung: UserModel-Eintrag anlegen
        user_model = UserModel(id=response.user.id)
        db.add(user_model)
        db.commit()
        db.refresh(user_model)
        return UserResponse(
            email=response.user.email,
            id=response.user.id
        )
    except Exception as e:
        print(f"[Auth][Register][Exception] {e}")
        print(f"[Auth][Register][Exception] Supabase response: {locals().get('response', None)}")
        print(f"[Auth][Register][Exception] Supabase error: {getattr(locals().get('response', None), 'error', None)}")
        print(f"[Auth][Register][Exception] Supabase user: {getattr(locals().get('response', None), 'user', None)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login with email and password (JSON body)."""
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        if not response.user:
            print(f"[Auth][Login][Error] Supabase response: {response}")
            print(f"[Auth][Login][Error] Supabase error: {getattr(response, 'error', None)}")
            print(f"[Auth][Login][Error] Supabase user: {getattr(response, 'user', None)}")
            print(f"[Auth][Login][Error] Supabase session: {getattr(response, 'session', None)}")
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
    except Exception as e:
        print(f"[Auth][Login][Exception] {e}")
        print(f"[Auth][Login][Exception] Supabase response: {locals().get('response', None)}")
        print(f"[Auth][Login][Exception] Supabase error: {getattr(locals().get('response', None), 'error', None)}")
        print(f"[Auth][Login][Exception] Supabase user: {getattr(locals().get('response', None), 'user', None)}")
        print(f"[Auth][Login][Exception] Supabase session: {getattr(locals().get('response', None), 'session', None)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password (form data)."""
    try:
        supabase = await get_supabase_client()
        response = await supabase.auth.sign_in_with_password({
            "email": form_data.username,
            "password": form_data.password
        })
        if not response.user:
            print(f"[Auth][Login-Form][Error] Supabase response: {response}")
            print(f"[Auth][Login-Form][Error] Supabase error: {getattr(response, 'error', None)}")
            print(f"[Auth][Login-Form][Error] Supabase user: {getattr(response, 'user', None)}")
            print(f"[Auth][Login-Form][Error] Supabase session: {getattr(response, 'session', None)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return TokenResponse(
            access_token=response.session.access_token,
            user=UserResponse(
                email=response.user.email,
                id=response.user.id
            )
        )
    except Exception as e:
        print(f"[Auth][Login-Form][Exception] {e}")
        print(f"[Auth][Login-Form][Exception] Supabase response: {locals().get('response', None)}")
        print(f"[Auth][Login-Form][Exception] Supabase error: {getattr(locals().get('response', None), 'error', None)}")
        print(f"[Auth][Login-Form][Exception] Supabase user: {getattr(locals().get('response', None), 'user', None)}")
        print(f"[Auth][Login-Form][Exception] Supabase session: {getattr(locals().get('response', None), 'session', None)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """
    Logout the current user. Der Access-Token muss im Authorization-Header als Bearer-Token mitgesendet werden.
    """
    return {"message": "Successfully logged out"} 

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(data: RefreshTokenRequest):
    """
    Refresh the access token using a refresh token.
    """
    try:
        supabase = await get_supabase_client()
        session = await supabase.auth.refresh_session(data.refresh_token)
        # print(f"session: {session}")
        # print(f"session.access_token: {getattr(session, 'access_token', None)}")
        # print(f"session.refresh_token: {getattr(session, 'refresh_token', None)}")
        # print(f"session.user: {getattr(session, 'user', None)}")
        # print(f"session.error: {getattr(session, 'error', None)}")
        if (
            not session
            or getattr(session, 'error', None)
            or getattr(session, 'access_token', None) is None
            or getattr(session, 'user', None) is None
        ):
            print(f"[Auth][Refresh][Error] Invalid session or missing attributes: {session}")
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        return RefreshTokenResponse(
            access_token=session.access_token,
            refresh_token=session.refresh_token,
            user=UserResponse(
                email=session.user.email,
                id=session.user.id
            )
        )
    except Exception as e:
        print(f"[Auth][Refresh][Exception] {e}")
        raise HTTPException(status_code=401, detail="Could not refresh token")