from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.supabase import get_supabase_client
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import time

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login-form")


class User(BaseModel):
    id: str
    email: EmailStr
    role: Optional[str] = None

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Dependency to get the current user from the JWT token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Verify token with Supabase (GoTrue)
        supabase = get_supabase_client()
        # The token will be verified by Supabase
        user = supabase.auth.get_user(token)
        
        if not user or not user.user:
            raise credentials_exception
            
        # Return the user data
        return User(
            id=user.user.id,
            email=user.user.email,
            role=user.user.app_metadata.get("role") if user.user.app_metadata else None
        )
        
    except JWTError:
        raise credentials_exception 