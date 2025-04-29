from fastapi import APIRouter, Depends, HTTPException, status
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
    token_type: str = "bearer"
    user: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login-form")

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserRegister, db: Session = Depends(get_session)):
    """
    Register a new user with Supabase Auth. Returns only user info, no token.
    """
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_up({
            "email": user_data.email,
            "password": user_data.password
        })
        if not response.user:
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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """Login with email and password (JSON body)."""
    try:
        supabase = get_supabase_client()
        response = supabase.auth.sign_in_with_password({
            "email": login_data.email,
            "password": login_data.password
        })
        if not response.user:
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
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

@router.post("/login-form", response_model=TokenResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login with email and password (form data)."""
    supabase = get_supabase_client()
    response = supabase.auth.sign_in_with_password({
        "email": form_data.username,
        "password": form_data.password
    })
    if not response.user:
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