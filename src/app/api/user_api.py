from fastapi import APIRouter, Depends, HTTPException, status
from app.db.user_repository import user_repository, UserCreate, UserUpdate
from app.core.auth import get_current_user, User
from typing import List
from uuid import UUID

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    """
    return current_user

@router.get("/{user_id}", response_model=User)
async def get_user(user_id: UUID, current_user: User = Depends(get_current_user)):
    """
    Get a user by ID
    """
    user = await user_repository.get(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return User(id=str(user.id), email=user.email)

@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: UUID, 
    user_update: UserUpdate, 
    current_user: User = Depends(get_current_user)
):
    """
    Update a user
    """
    # Check if the user is updating their own profile
    if str(user_id) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user"
        )
    
    updated_user = await user_repository.update(id=user_id, obj_in=user_update)
    if not updated_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return User(id=str(updated_user.id), email=updated_user.email) 