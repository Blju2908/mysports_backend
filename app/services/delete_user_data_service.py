from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from uuid import UUID
import logging

from app.models.user_model import UserModel
from app.models.training_plan_model import TrainingPlan
from app.models.app_feedback_model import AppFeedbackModel
from app.models.workout_feedback_model import WorkoutFeedback

logger = logging.getLogger("delete_user_service")


async def delete_all_user_data(user_id: UUID, db: AsyncSession) -> None:
    """
    Deletes ALL user data but keeps the user account intact.
    
    Deletion Order:
    1. App Feedback (manual - no CASCADE defined)
    2. Workout Feedback (manual - has CASCADE but explicit delete for clarity)
    3. Training Plan (triggers CASCADE: workouts → blocks → exercises → sets)
    4. Reset User Model data (but keep the user account)
    
    The user account itself (UserModel and Supabase Auth) remains active.
    
    Args:
        user_id: UUID of the user whose data to delete
        db: Async database session
        
    Raises:
        HTTPException: If user not found or deletion fails
    """
    logger.info(f"[DeleteUserData] Starting deletion for user_id: {user_id}")
    
    try:
        # First, verify user exists
        user_query = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            logger.warning(f"[DeleteUserData] User not found: {user_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        logger.info(f"[DeleteUserData] User found, starting data deletion for: {user_id}")
        
        # 1. Delete App Feedback (manual - no CASCADE)
        app_feedback_delete = delete(AppFeedbackModel).where(AppFeedbackModel.user_id == user_id)
        app_feedback_result = await db.execute(app_feedback_delete)
        logger.info(f"[DeleteUserData] Deleted {app_feedback_result.rowcount} app feedback records")
        
        # 2. Delete Workout Feedback (manual for explicit control)
        workout_feedback_delete = delete(WorkoutFeedback).where(WorkoutFeedback.user_id == user_id)
        workout_feedback_result = await db.execute(workout_feedback_delete)
        logger.info(f"[DeleteUserData] Deleted {workout_feedback_result.rowcount} workout feedback records")
        
        # 3. Delete Training Plan (triggers CASCADE)
        # TrainingPlan has user_id FK, so we delete by user_id
        # This will CASCADE delete: workouts → blocks → exercises → sets
        training_plan_delete = delete(TrainingPlan).where(TrainingPlan.user_id == user_id)
        training_plan_result = await db.execute(training_plan_delete)
        logger.info(f"[DeleteUserData] Deleted {training_plan_result.rowcount} training plan(s) and all cascaded data")
        
        # 4. Reset User Model data (onboarding flag)
        from sqlalchemy import update
        from datetime import datetime
        user_update = (
            update(UserModel)
            .where(UserModel.id == user_id)
            .values(
                onboarding_completed=False,
                updated_at=datetime.utcnow()
            )
        )
        user_result = await db.execute(user_update)
        logger.info(f"[DeleteUserData] Reset user onboarding status")
        
        # Commit all local database changes
        await db.commit()
        logger.info(f"[DeleteUserData] Successfully committed all data deletions for user: {user_id}")
        
        logger.info(f"[DeleteUserData] Successfully completed all data deletions for user: {user_id} (account remains active)")
        
    except HTTPException:
        # Re-raise HTTP exceptions
        await db.rollback()
        raise
    except Exception as e:
        # Rollback on any error
        await db.rollback()
        logger.error(f"[DeleteUserData] Error deleting user data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user data: {str(e)}"
        )





async def check_user_exists(user_id: UUID, db: AsyncSession) -> bool:
    """
    Helper function to check if a user exists in the database.
    
    Args:
        user_id: UUID of the user to check
        db: Async database session
        
    Returns:
        bool: True if user exists, False otherwise
    """
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    return user is not None 