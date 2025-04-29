from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join
from typing import List, Optional
from sqlalchemy.orm import selectinload
from datetime import datetime

from app.models.workout_model import Workout, WorkoutStatus
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.schemas.workout_schema import WorkoutResponseSchema, WorkoutDetailResponseSchema, BlockResponseSchema, ActivityBlockPayloadSchema, ActivitySetSchema
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.block_model import Block, BlockStatus
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from app.models.training_history import ActivityLog
from app.services.workout_service import get_workout_details

router = APIRouter(
    prefix="/workouts",
    tags=["workouts"],
)


@router.get("/", response_model=List[WorkoutResponseSchema])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None
):
    """
    Get all workouts for the current user.
    Optionally filter by status (COMPLETED, INCOMPLETE, etc.)
    """
    # First get the training plans the user is following
    follower_query = select(TrainingPlanFollower.training_plan_id).where(
        TrainingPlanFollower.user_id == current_user.id
    )
    result = await db.execute(follower_query)
    training_plan_ids = [row[0] for row in result.all()]
    
    if not training_plan_ids:
        return []  # User is not following any training plans
    
    # Then get the workouts for those training plans
    workout_query = select(Workout).where(
        Workout.training_plan_id.in_(training_plan_ids)
    ).order_by(Workout.date.desc())
    
    # Apply status filter if provided
    if status:
        try:
            workout_status = WorkoutStatus(status.lower())
            workout_query = workout_query.where(Workout.status == workout_status)
        except ValueError:
            # Invalid status provided - ignore the filter
            pass
    
    result = await db.execute(workout_query)
    workouts = result.scalars().all()
    
    return workouts


@router.get("/{workout_id}", response_model=WorkoutDetailResponseSchema)
async def get_workout_detail(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific workout including all blocks and exercises.
    Uses the workout service for logic and authorization.
    """
    # Call the service function, exceptions will propagate
    workout = await get_workout_details(
        workout_id=workout_id, 
        user_id=current_user.id, 
        db=db
    )
    return workout 


@router.get("/{workout_id}/blocks/{block_id}", response_model=BlockResponseSchema)
async def get_block_detail(
    workout_id: int,
    block_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed information about a specific block including all exercises and sets.
    Ensures the block belongs to a workout the user has access to.
    """
    # 1. Prüfen, ob der User Zugriff auf das Workout hat
    follower_query = select(TrainingPlanFollower.training_plan_id).where(
        TrainingPlanFollower.user_id == current_user.id
    )
    result = await db.execute(follower_query)
    training_plan_ids = [row[0] for row in result.all()]

    if not training_plan_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no access to any training plans"
        )

    # 2. Den spezifischen Block holen und sicherstellen, dass er zum richtigen Workout gehört,
    #    auf das der User Zugriff hat. Lade Übungen und Sets.
    block_query = select(Block).options(
        selectinload(Block.exercises).selectinload(Exercise.sets)
    ).join(Workout, Block.workout_id == Workout.id).where(
        Block.id == block_id,
        Block.workout_id == workout_id,
        Workout.training_plan_id.in_(training_plan_ids)
    )
    
    result = await db.execute(block_query)
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found or user does not have access to the parent workout"
        )

    return block


@router.post("/{workout_id}/blocks/{block_id}/save-activity", status_code=status.HTTP_201_CREATED)
async def save_activity_block_endpoint(
    workout_id: int,
    block_id: int,
    payload: ActivityBlockPayloadSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Saves the completed sets of a block as activity logs in the training history.
    Updates the block status to 'completed'.
    """
    # 1. Verify user access to the workout and get the block
    follower_query = select(TrainingPlanFollower.training_plan_id).where(
        TrainingPlanFollower.user_id == current_user.id
    )
    f_result = await db.execute(follower_query)
    training_plan_ids = [row[0] for row in f_result.all()]

    if not training_plan_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no access to any training plans"
        )

    # Fetch the specific block and verify it belongs to the workout and user
    block_query = select(Block).join(Workout, Block.workout_id == Workout.id).where(
        Block.id == block_id,
        Block.workout_id == workout_id,
        Workout.training_plan_id.in_(training_plan_ids)
    )
    b_result = await db.execute(block_query)
    block_to_update = b_result.scalar_one_or_none()

    if not block_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found or user does not have access"
        )
        
    # Prevent overwriting if already completed (optional, depends on desired behavior)
    if block_to_update.status == BlockStatus.complete:
         raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Block is already marked as completed."
        )

    # 2. Create ActivityLog entries for each set in the payload
    activity_logs: List[ActivityLog] = []
    current_timestamp = datetime.utcnow()
    for activity_set in payload.sets:
        # Ensure the set ID exists if needed for linking, otherwise rely on other fields
        log_entry = ActivityLog(
            user_id=current_user.id,
            timestamp=current_timestamp,
            exercise_name=activity_set.exercise_name,
            set_id=activity_set.id,
            weight=activity_set.weight,
            reps=activity_set.reps,
            duration=activity_set.duration,
            distance=activity_set.distance,
            speed=activity_set.speed,
            rest_time=activity_set.rest_time,
        )
        activity_logs.append(log_entry)
        db.add(log_entry)

    # 3. Update the block status to completed
    block_to_update.status = BlockStatus.complete
    db.add(block_to_update)

    # 4. Commit the transaction
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error saving activity block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save activity log."
        )

    return None


@router.delete("/{workout_id}", status_code=204)
async def delete_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Löscht ein Workout mittels direktem SQL-Statement.
    Alle abhängigen Objekte werden automatisch durch ON DELETE CASCADE gelöscht.
    """
    # Prüfe, ob das Workout dem User gehört (über TrainingPlanFollower)
    follower_query = select(TrainingPlanFollower.training_plan_id).where(
        TrainingPlanFollower.user_id == current_user.id
    )
    result = await db.execute(follower_query)
    training_plan_ids = [row[0] for row in result.all()]
    
    if not training_plan_ids:
        raise HTTPException(status_code=404, detail="Kein Workout gefunden.")
    
    # Prüfe, ob das Workout existiert und zum User gehört
    workout_query = select(Workout).where(
        Workout.id == workout_id,
        Workout.training_plan_id.in_(training_plan_ids)
    )
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout nicht gefunden oder kein Zugriff.")
    
    # Direkt mit SQL löschen, umgeht SQLAlchemy ORM Beziehungen
    from sqlalchemy import text
    await db.execute(text(f"DELETE FROM workouts WHERE id = :workout_id"), {"workout_id": workout_id})
    await db.commit()
    
    return None 