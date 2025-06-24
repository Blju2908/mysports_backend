# backend/app/routers/training_plan.py - SIMPLIFIED VERSION
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import select
from app.models.training_plan_model import TrainingPlan
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from app.models.user_model import UserModel
from typing import Dict, Any
import json
from datetime import date

router = APIRouter(tags=["training-plan"])
logger = logging.getLogger("training_plan")

# 🔧 HELPER FUNCTIONS - Reduce duplication
async def get_or_create_user(db: AsyncSession, user_id: UUID) -> UserModel:
    """Get user from DB or create if doesn't exist"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        user = UserModel(id=user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user

async def get_or_create_training_plan(db: AsyncSession, user: UserModel) -> TrainingPlan:
    """Get user's training plan or create empty one"""
    if user.training_plan_id:
        # Try to get existing plan
        plan_query = select(TrainingPlan).where(TrainingPlan.id == user.training_plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        
        if plan:
            return plan
    
    # Create new empty plan with defaults
    new_plan = TrainingPlan(
        equipment=[],  # Changed from empty string to empty array
        session_duration=45,
        training_frequency=3,
        fitness_level=3,
        experience_level=3,
        include_cardio=True
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    
    # Link user to plan
    user.training_plan_id = new_plan.id
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return new_plan

def safe_json_serialize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Safely serialize data with date objects"""
    def date_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    # Convert to JSON string and back to ensure all dates are serialized
    json_str = json.dumps(data, default=date_serializer)
    return json.loads(json_str)

# 🎯 SIMPLIFIED ENDPOINTS
@router.get("/mine", response_model=Dict[str, Any])
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get current user's training plan"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Get or create user
        user = await get_or_create_user(db, user_uuid)
        
        # Get or create training plan
        plan = await get_or_create_training_plan(db, user)
        
        # Convert to frontend format
        plan_dict = plan.model_dump()
        schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[Get] Successfully retrieved plan for user {user_uuid}")
        return schema.to_frontend_format()
        
    except Exception as e:
        logger.error(f"[Get] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Laden des Trainingsplans: {str(e)}"
        )

@router.put("/mine", response_model=Dict[str, Any])
async def update_my_training_plan(
    plan_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update current user's training plan"""
    try:
        logger.info(f"[Update] Received data: {plan_data}")
        
        user_uuid = UUID(current_user.id)
        
        # Get or create user
        user = await get_or_create_user(db, user_uuid)
        
        # Get or create training plan
        plan = await get_or_create_training_plan(db, user)
        
        # Convert from frontend format and validate
        schema = TrainingPlanSchema.from_frontend_format(plan_data)
        
        # Update plan with validated data
        update_data = schema.model_dump(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            if key != "id":  # Never update ID
                setattr(plan, key, value)
        
        # Save changes
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Return updated plan
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[Update] Successfully updated plan {plan.id} for user {user_uuid}")
        return response_schema.to_frontend_format()
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[Update] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Aktualisieren des Trainingsplans: {str(e)}"
        )