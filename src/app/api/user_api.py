from fastapi import APIRouter, Depends, HTTPException, status
from app.db.user_repository import user_repository, UserUpdate
from app.core.auth import get_current_user, User
from uuid import UUID
from app.core.supabase import get_supabase_client

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user