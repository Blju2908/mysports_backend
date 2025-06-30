# backend/app/api/v1/training_plan_endpoint.py - UPDATED FOR NEW RELATIONSHIP
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema
from sqlalchemy.ext.asyncio import AsyncSession

from uuid import UUID
from typing import Dict, Any

router = APIRouter(tags=["training-plan"])


@router.get("/mine", response_model=TrainingPlanSchema)
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ BEST PRACTICE: SQLModel One-Liner - Direct TrainingPlan query via user_id Foreign Key
    """
    # ✅ SQLModel One-Liner: Direkt TrainingPlan über user_id laden
    training_plan = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.user_id == UUID(current_user.id))
    )
    
    if not training_plan:
        # Kein TrainingPlan vorhanden - erstellen mit Defaults
        # Stelle sicher, dass User existiert
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == UUID(current_user.id))
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # User existiert auch nicht - erstellen
            user = UserModel(id=UUID(current_user.id))
            db.add(user)
        
        # TrainingPlan mit Defaults erstellen
        training_plan = TrainingPlan(
            user_id=UUID(current_user.id),
            equipment=[],
            workout_styles=[],
            session_duration=45,
            training_frequency=3,
            fitness_level=3,
            experience_level=3
        )
        
        db.add(training_plan)
        
        try:
            await db.commit()
            await db.refresh(training_plan)
            return TrainingPlanSchema.model_validate(training_plan)
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating training plan: {str(e)}")
    
    return TrainingPlanSchema.model_validate(training_plan)


@router.put("/mine", response_model=TrainingPlanSchema)
async def update_my_training_plan(
    plan_update: TrainingPlanSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ BEST PRACTICE: SQLModel One-Liner - Direct TrainingPlan query and upsert via user_id Foreign Key
    """
    # ✅ SQLModel One-Liner: Direkt TrainingPlan über user_id laden
    training_plan = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.user_id == UUID(current_user.id))
    )
    
    if not training_plan:
        # Kein TrainingPlan vorhanden - erstellen
        # Stelle sicher, dass User existiert
        user_result = await db.execute(
            select(UserModel).where(UserModel.id == UUID(current_user.id))
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            # User existiert auch nicht - erstellen
            user = UserModel(id=UUID(current_user.id))
            db.add(user)
        
        # Neuen TrainingPlan erstellen
        training_plan = TrainingPlan(user_id=UUID(current_user.id))
        db.add(training_plan)
    
    # ✅ Update alle Felder aus dem Request (außer user_id)
    update_data = plan_update.model_dump(exclude_unset=True, exclude={"id", "user_id"})
    for field, value in update_data.items():
        setattr(training_plan, field, value)
    
    try:
        await db.commit()
        await db.refresh(training_plan)
        return TrainingPlanSchema.model_validate(training_plan)
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error upserting training plan: {str(e)}")