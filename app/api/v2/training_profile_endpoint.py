# backend/app/api/v2/training_profile_endpoint.py
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.models.training_plan_model import TrainingProfile # Reusing TrainingProfile model
from app.models.user_model import UserModel
from app.schemas.training_plan_schemas import TrainingProfileCreate, TrainingProfileRead # Reusing schemas
from app.core.auth import get_current_user, User
from app.db.session import get_session
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List

router = APIRouter(tags=["training-profiles"])

@router.post("/", response_model=TrainingProfileRead, status_code=201)
async def create_training_profile(
    profile_create: TrainingProfileCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> TrainingProfile:
    """
    Creates a new training profile for the current user.
    """
    user_id = UUID(current_user.id)
    
    # If the new profile is set as primary, ensure existing primary profiles are set to false
    if profile_create.is_primary:
        existing_primary_profile = await db.scalar(
            select(TrainingProfile)
            .where(TrainingProfile.user_id == user_id, TrainingProfile.is_primary == True)
        )
        if existing_primary_profile:
            existing_primary_profile.is_primary = False
            db.add(existing_primary_profile) # Mark for update
    
    new_profile = TrainingProfile(**profile_create.model_dump(), user_id=user_id)
    db.add(new_profile)
    
    try:
        await db.commit()
        await db.refresh(new_profile)
        return new_profile
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating training profile: {str(e)}")

@router.get("/all", response_model=List[TrainingProfileRead])
async def get_all_my_training_profiles(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> List[TrainingProfile]:
    """
    Retrieves all training profiles for the current user.
    If no profiles exist, it creates a default primary profile and returns it.
    """
    user_id = UUID(current_user.id)
    
    # Get all profiles for the user
    result = await db.execute(
        select(TrainingProfile)
        .where(TrainingProfile.user_id == user_id)
        .order_by(TrainingProfile.id)
    )
    training_profiles = result.scalars().all()
    
    if not training_profiles:
        # No training profiles found - create a default primary profile
        # Ensure user exists
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == UUID(current_user.id))
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # User does not exist - create user first
            user = UserModel(id=UUID(current_user.id))
            db.add(user)
        
        # Create default TrainingProfile
        default_profile = TrainingProfile(
            user_id=UUID(current_user.id),
            name="Mein Trainingsplan",
            is_primary=True,
            equipment="",
            equipment_llm_context="",
            equipment_details=""
        )
        
        db.add(default_profile)
        
        try:
            await db.commit()
            await db.refresh(default_profile)
            return [default_profile]
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating default training profile: {str(e)}")
    
    return list(training_profiles)

@router.get("/mine", response_model=TrainingProfileRead)
async def get_my_primary_training_profile(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> TrainingProfile:
    """
    Retrieves the primary training profile for the current user.
    If no primary profile exists, it creates one with default values and returns it.
    """
    user_id = UUID(current_user.id)
    training_profile = await db.scalar(
        select(TrainingProfile)
        .where(TrainingProfile.user_id == user_id, TrainingProfile.is_primary == True)
    )
    
    if not training_profile:
        # No training profile found - create with defaults
        # Ensure user exists
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == UUID(current_user.id))
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # User does not exist - create user first
            user = UserModel(id=UUID(current_user.id))
            db.add(user)
        
        # Create TrainingProfile with defaults
        training_profile = TrainingProfile(
            user_id=UUID(current_user.id),
            name="Mein Trainingsplan",
            is_primary=True, # Ensure it's marked as primary
            equipment="",
            equipment_llm_context="",
            equipment_details=""
        )
        
        db.add(training_profile)
        
        try:
            await db.commit()
            await db.refresh(training_profile)
            return training_profile
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating training profile: {str(e)}")
    
    return training_profile

@router.put("/{profile_id}", response_model=TrainingProfileRead)
async def update_training_profile(
    profile_id: int,
    profile_update: TrainingProfileCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> TrainingProfile:
    """
    Updates a specific training profile for the current user.
    """
    user_id = UUID(current_user.id)
    training_profile = await db.scalar(
        select(TrainingProfile)
        .where(TrainingProfile.id == profile_id, TrainingProfile.user_id == user_id)
    )

    if not training_profile:
        raise HTTPException(status_code=404, detail="Training profile not found for this user.")
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(training_profile, field, value)
        
    try:
        await db.commit()
        await db.refresh(training_profile)
        return training_profile
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating training profile: {str(e)}")

@router.put("/mine", response_model=TrainingProfileRead)
async def update_my_primary_training_profile(
    profile_update: TrainingProfileCreate,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> TrainingProfile:
    """
    Updates the primary training profile for the current user.
    If no primary profile exists, it returns a 404.
    """
    user_id = UUID(current_user.id)
    training_profile = await db.scalar(
        select(TrainingProfile)
        .where(TrainingProfile.user_id == user_id, TrainingProfile.is_primary == True)
    )

    if not training_profile:
        raise HTTPException(status_code=404, detail="Primary training profile not found for this user.")
    
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(training_profile, field, value)
        
    try:
        await db.commit()
        await db.refresh(training_profile)
        return training_profile
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating training profile: {str(e)}")

@router.delete("/{profile_id}", status_code=204)
async def delete_training_profile(
    profile_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Deletes a training profile for the current user.
    Cannot delete if it's the only profile for the user.
    """
    user_id = UUID(current_user.id)
    
    # Check how many profiles the user has
    profile_count = await db.scalar(
        select(TrainingProfile)
        .where(TrainingProfile.user_id == user_id)
    )
    
    if not profile_count:
        raise HTTPException(status_code=404, detail="No training profiles found for this user.")
    
    # Count total profiles for user
    total_profiles = len((await db.execute(
        select(TrainingProfile).where(TrainingProfile.user_id == user_id)
    )).scalars().all())
    
    if total_profiles <= 1:
        raise HTTPException(status_code=400, detail="Cannot delete the only training profile.")
    
    # Find the specific profile to delete
    training_profile = await db.scalar(
        select(TrainingProfile)
        .where(TrainingProfile.id == profile_id, TrainingProfile.user_id == user_id)
    )

    if not training_profile:
        raise HTTPException(status_code=404, detail="Training profile not found for this user.")
    
    try:
        await db.delete(training_profile)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting training profile: {str(e)}") 