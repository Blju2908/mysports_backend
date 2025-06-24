from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select 
from typing import Optional
from uuid import UUID

from app.models.workout_model import Workout
from app.models.workout_feedback_model import WorkoutFeedback
from app.models.user_model import UserModel
from app.schemas.workout_feedback_schema import WorkoutFeedbackSchema, WorkoutFeedbackResponseSchema
from app.core.auth import get_current_user, User
from app.db.session import get_session

router = APIRouter(tags=["feedback"])


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=WorkoutFeedbackResponseSchema)
async def submit_workout_feedback(
    feedback: WorkoutFeedbackSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SQLMODEL BEST PRACTICE: Kombinierte Security + UPSERT mit Auto-Serialization
    """
    # 🔥 STEP 1: Combined Security + Existing Feedback Check
    feedback_query = (
        select(WorkoutFeedback)
        .join(Workout, WorkoutFeedback.workout_id == Workout.id)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            WorkoutFeedback.workout_id == feedback.workout_id,
            WorkoutFeedback.user_id == UUID(current_user.id),
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)
        )
    )
    result = await db.execute(feedback_query)
    existing_feedback = result.scalar_one_or_none()
    
    if existing_feedback:
        # ✅ UPDATE: Smart field updates 
        for field, value in feedback.model_dump(exclude_unset=True).items():
            setattr(existing_feedback, field, value)
        
        await db.commit()
        await db.refresh(existing_feedback)
        return WorkoutFeedbackResponseSchema.model_validate(existing_feedback)
    
    # 🔥 STEP 2: Verify workout exists for CREATE (wenn kein existing feedback)
    workout_exists = await db.execute(
        select(Workout)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            Workout.id == feedback.workout_id,
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)
        )
    )
    
    if not workout_exists.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Workout not found or access denied")
    
    # ✅ CREATE: Simple object creation + Auto-Serialization
    new_feedback = WorkoutFeedback(**feedback.model_dump(), user_id=UUID(current_user.id))
    db.add(new_feedback)
    await db.commit()
    await db.refresh(new_feedback)
    
    return WorkoutFeedbackResponseSchema.model_validate(new_feedback)


@router.get("/{workout_id}", response_model=Optional[WorkoutFeedbackResponseSchema])
async def get_workout_feedback(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SQLMODEL BEST PRACTICE: Kombinierte Security Query + Auto-Serialization
    """
    feedback_query = (
        select(WorkoutFeedback)
        .join(Workout, WorkoutFeedback.workout_id == Workout.id)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            WorkoutFeedback.workout_id == workout_id,
            WorkoutFeedback.user_id == UUID(current_user.id),
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)
        )
    )
    
    result = await db.execute(feedback_query)
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        return None
    
    return WorkoutFeedbackResponseSchema.model_validate(feedback) 