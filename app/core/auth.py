from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.supabase import get_supabase_client
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import time
import logging

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v2/auth/login-form")

logger = logging.getLogger("auth")

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
        logger.info(f"[get_current_user] Validating token: {token[:8]}...")
        
        # ✅ WICHTIG: use_service_role=True für Backend Token-Validierung
        supabase = await get_supabase_client(use_service_role=True)
        user_response = await supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            logger.warning(f"[get_current_user] No user found for token: {token[:8]}...")
            raise credentials_exception
            
        user = user_response.user
        logger.info(f"[get_current_user] User validated: {user.email}")
        
        return User(
            id=user.id,
            email=user.email,
            role=user.app_metadata.get("role") if user.app_metadata else None
        )
        
    except JWTError as e:
        logger.error(f"[get_current_user] JWTError: {e}")
        raise credentials_exception
    except Exception as e:
        logger.error(f"[get_current_user] Exception: {e}")
        raise credentials_exception 

async def get_current_user_optional(request: Request) -> Optional[User]:
    """
    Versucht den aktuellen User zu extrahieren, gibt None zurück falls nicht authentifiziert.
    Für Middleware-Verwendung ohne Exceptions.
    """
    try:
        # Authorization Header prüfen
        authorization = request.headers.get("authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return None
        
        token = authorization.split("")[1]
        
        # ✅ WICHTIG: use_service_role=True auch hier
        supabase = await get_supabase_client(use_service_role=True)
        user_response = await supabase.auth.get_user(token)
        
        if not user_response or not user_response.user:
            return None
            
        user = user_response.user
        return User(
            id=user.id,
            email=user.email,
            role=user.app_metadata.get("role") if user.app_metadata else None
        )
        
    except Exception:
        return None