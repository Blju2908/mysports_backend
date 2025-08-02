from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Optional
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator
from uuid import UUID, uuid4
import os
import json

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus

from app.models.user_model import UserModel
from app.schemas.workout_schema import (
    WorkoutListRead,
    WorkoutWithBlocksRead,
    BlockRead,
    BlockSaveResponse,
    BlockInput,
    SetRead,
    SetUpdate,
    WorkoutStatusEnum,
    ExerciseRead,
    ExerciseHistoryResponse
)

from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.services.workout_service import get_latest_workouts_with_details, get_exercises_with_done_sets_only, get_exercise_history_for_workout

# --- API Specific Request Payloads ---

# Payload for updating a single set's status and execution data
class SetStatusUpdatePayload(BaseModel):
    status: SetStatus
    completed_at: datetime | None = None
    weight: float | None = None
    reps: int | None = None
    duration: int | None = None
    distance: float | None = None
    notes: str | None = None
    
    @field_validator('completed_at')
    @classmethod
    def make_datetime_naive(cls, v: datetime | None) -> datetime | None:
        """✅ Automatisch timezone-aware datetimes zu naive konvertieren"""
        if v is not None and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

router = APIRouter(tags=["workouts"])


@router.get("/", response_model=List[WorkoutListRead])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SQLModel Best Practice: Direct user-workout relationship with efficient DB-level status calculation
    """
    # ✅ SQLModel One-Liner: Direct user query
    user = await db.scalar(
        select(UserModel)
        .options(selectinload(UserModel.training_plan))
        .where(UserModel.id == UUID(current_user.id))
    )

    if not user or not user.training_plan:
        return []

    # ✅ Subqueries for efficient status calculation without loading relationships
    total_sets_subquery = (
        select(func.count(Set.id))
        .select_from(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .where(Block.workout_id == Workout.id)
    ).scalar_subquery()

    done_sets_subquery = (
        select(func.count(Set.id))
        .select_from(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .where(
            Block.workout_id == Workout.id,
            Set.status == SetStatus.done
        )
    ).scalar_subquery()

    # ✅ Status calculation in database
    status_case = case(
        (total_sets_subquery == 0, "not_started"),
        (done_sets_subquery == total_sets_subquery, "done"),
        (done_sets_subquery > 0, "started"),
        else_="not_started"
    ).label("computed_status")

    # ✅ Direct user_id query instead of training_plan_id
    workout_query = (
        select(Workout, status_case)
        .where(Workout.user_id == UUID(current_user.id))  # ✅ Direct user relationship!
        .order_by(Workout.date_created.desc())
    )

    result = await db.execute(workout_query)
    workout_tuples = result.all()

    # ✅ Manual mapping with computed status
    workouts = []
    for workout_obj, computed_status in workout_tuples:
        workout_dict = {
            "id": workout_obj.id,
            "training_plan_id": workout_obj.training_plan_id,
            "name": workout_obj.name,
            "date_created": workout_obj.date_created,
            "description": workout_obj.description,
            "duration": workout_obj.duration,
            "focus": workout_obj.focus,
            "notes": workout_obj.notes,
            "status": computed_status  # ✅ Directly computed by DB!
        }
        workouts.append(WorkoutListRead(**workout_dict))

    return workouts


@router.get("/latest-workouts", response_model=List[WorkoutWithBlocksRead])
async def get_latest_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Einfache Workout-Erstellung mit Auto-Serialization
    """
    workouts = await get_latest_workouts_with_details(db=db, user_id=UUID(current_user.id))

    # create directory outputs if it doesn't exist
    os.makedirs("outputs", exist_ok=True)
    # store the workouts in the directory outputs with the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    with open(f"outputs/latest_workouts_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump([WorkoutWithBlocksRead.model_validate(w).model_dump(mode='json') for w in workouts], f, default=str, ensure_ascii=False)

    return workouts

@router.get("/exercises-with-done-sets", response_model=List[ExerciseRead])
async def get_user_exercises_with_done_sets(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves all exercises for the current user that have at least one 'done' set,
    including only the 'done' sets for each exercise.
    Exercises without any 'done' sets are excluded.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    exercises = await get_exercises_with_done_sets_only(
        db=db,
        current_user_id=UUID(current_user.id)
    )
    with open(f"outputs/exercises_with_done_sets_{timestamp}.json", "w", encoding='utf-8') as f:
        json.dump([ExerciseRead.model_validate(e).model_dump(mode='json') for e in exercises], f, default=str, ensure_ascii=False)
    return exercises


@router.get("/{workout_id}/exercise-history", response_model=ExerciseHistoryResponse)
async def get_workout_exercise_history(
    workout_id: int,
    limit_per_exercise: int = 10,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieves exercise history for all exercises in a specific workout.
    Returns the last N completed sets for each exercise across all user's workouts.
    
    Args:
        workout_id: The ID of the workout to get exercise history for
        limit_per_exercise: Maximum number of history entries per exercise (default: 10)
    
    Returns:
        Exercise history grouped by exercise name
    """
    # First verify the user has access to this workout
    workout = await db.scalar(
        select(Workout)
        .where(
            Workout.id == workout_id,
            Workout.user_id == UUID(current_user.id)
        )
    )
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found or access denied")
    
    # Get exercise history
    exercise_histories = await get_exercise_history_for_workout(
        db=db,
        workout_id=workout_id,
        user_id=UUID(current_user.id),
        limit_per_exercise=limit_per_exercise
    )
    
    return ExerciseHistoryResponse(exercise_histories=exercise_histories)




@router.get("/{workout_id}", response_model=WorkoutWithBlocksRead)
async def get_workout_detail(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SQLModel Best Practice: Direct user-workout relationship with security check in query
    """
    # ✅ SQLModel One-Liner: Direct workout query with security check
    workout = await db.scalar(
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(
            Workout.id == workout_id,
            Workout.user_id == UUID(current_user.id)  # ✅ Direct user security check!
        )
    )
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found or access denied")
    
    # ✅ Use sorted blocks method from model
    if hasattr(workout, 'get_sorted_blocks'):
        workout.blocks = workout.get_sorted_blocks()
    
    return WorkoutWithBlocksRead.model_validate(workout)


@router.get("/{workout_id}/blocks/{block_id}", response_model=BlockRead)
async def get_block_detail(
    workout_id: int,
    block_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SQLModel Best Practice: Direct user-workout relationship with security in query
    """
    # ✅ SQLModel One-Liner: Direct block query with security check
    block = await db.scalar(
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            Workout.user_id == UUID(current_user.id),  # ✅ Direct user security check!
        )
    )

    if not block:
        raise HTTPException(status_code=404, detail="Block not found or access denied")

    return BlockRead.model_validate(block)


@router.post(
    "/{workout_id}/blocks/{block_id}",
    response_model=BlockSaveResponse
)
async def save_block(
    workout_id: int,
    block_id: int,
    block: BlockInput,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ OPTIMIZED: ID-preserving save_block to maintain frontend references
    Returns ID mapping for temporary IDs
    """
    # No longer need temp_id_mappings - we use UIDs now
    # ✅ SQLModel One-Liner: Direct block query with security check
    existing_block = await db.scalar(
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            Workout.user_id == UUID(current_user.id)  # ✅ Direct user security check!
        )
    )
    
    if not existing_block:
        raise HTTPException(status_code=404, detail="Block not found or access denied")

    try:
        # ✅ UPDATE: Block-Details aktualisieren (behält die gleiche ID)
        existing_block.name = block.name
        existing_block.description = block.description
        existing_block.notes = block.notes
        
        # ✅ SMART UID-BASED APPROACH: Update/Create/Delete based on UIDs
        existing_exercises_by_uid = {ex.uid: ex for ex in existing_block.exercises if ex.uid}
        # Fallback for legacy exercises without UIDs (will be removed after migration)
        existing_exercises_by_id = {str(ex.id): ex for ex in existing_block.exercises}
        incoming_exercise_uids = set()
        
        # Process each incoming exercise
        for ex_data in block.exercises:
            existing_exercise = None
            
            # First try to find by UID
            if hasattr(ex_data, 'uid') and ex_data.uid and ex_data.uid in existing_exercises_by_uid:
                existing_exercise = existing_exercises_by_uid[ex_data.uid]
                incoming_exercise_uids.add(ex_data.uid)
            # Fallback to ID-based lookup for backward compatibility
            elif hasattr(ex_data, 'id') and ex_data.id and str(ex_data.id) in existing_exercises_by_id:
                existing_exercise = existing_exercises_by_id[str(ex_data.id)]
                # Assign UID to legacy exercise if it doesn't have one
                if not existing_exercise.uid:
                    existing_exercise.uid = str(uuid4())
                    print(f"[Backend] Assigned UID {existing_exercise.uid} to legacy exercise {existing_exercise.id}")
            
            if existing_exercise:
                # ✅ UPDATE existing exercise
                existing_exercise.name = ex_data.name
                existing_exercise.description = ex_data.description
                existing_exercise.notes = ex_data.notes
                existing_exercise.superset_id = ex_data.superset_id
                existing_exercise.position = getattr(ex_data, "position", existing_exercise.position or 0)  # ✅ Position support
                
                # ✅ SMART SET HANDLING: Update/Create/Delete sets based on UIDs
                existing_sets_by_uid = {s.uid: s for s in existing_exercise.sets if s.uid}
                incoming_set_uids = set()
                
                for set_data in ex_data.sets:
                    if hasattr(set_data, 'uid') and set_data.uid and set_data.uid in existing_sets_by_uid:
                        # ✅ UPDATE existing set based on UID
                        existing_set = existing_sets_by_uid[set_data.uid]
                        print(f"[Backend] Updating existing set with UID: {set_data.uid}")
                        existing_set.weight = set_data.weight
                        existing_set.reps = set_data.reps
                        existing_set.duration = set_data.duration
                        existing_set.distance = set_data.distance
                        existing_set.rest_time = set_data.rest_time
                        existing_set.status = set_data.status
                        existing_set.completed_at = set_data.completed_at
                        existing_set.position = getattr(set_data, "position", existing_set.position or 0)  # ✅ Position support
                        
                        incoming_set_uids.add(set_data.uid)
                    else:
                        # ✅ CREATE new set (only if UID not found or not provided)
                        # Find max position and increment for new sets
                        existing_positions = [s.position or 0 for s in existing_exercise.sets if s.position is not None]
                        max_position = max(existing_positions) if existing_positions else -1
                        new_position = getattr(set_data, "position", max_position + 1)
                        
                        # Debug logging for UID handling
                        frontend_uid = getattr(set_data, 'uid', None)
                        generated_uid = frontend_uid if frontend_uid else str(uuid4())
                        print(f"[Backend] Creating new set - Frontend UID: {frontend_uid}, Using UID: {generated_uid}")
                        
                        new_set = Set(
                            uid=generated_uid,  # Use frontend UID or generate new
                            exercise_id=existing_exercise.id,
                            weight=set_data.weight,
                            reps=set_data.reps,
                            duration=set_data.duration,
                            distance=set_data.distance,
                            rest_time=set_data.rest_time,
                            status=set_data.status,
                            completed_at=set_data.completed_at,
                            position=new_position  # ✅ Position support
                        )
                        db.add(new_set)
                        
                        # No need for temp ID mapping anymore - we use UIDs
                        await db.flush()  # Ensure the set gets an ID
                
                # ✅ DELETE sets that are no longer present (based on UIDs)
                for existing_set in existing_exercise.sets:
                    if existing_set.uid and existing_set.uid not in incoming_set_uids:
                        print(f"[Backend] Deleting set with UID: {existing_set.uid} (not in incoming UIDs)")
                        await db.delete(existing_set)
                        
            else:
                # ✅ CREATE new exercise (only if no valid ID or ID not found)
                # Find max position and increment for new exercises
                existing_exercise_positions = [ex.position or 0 for ex in existing_block.exercises if ex.position is not None]
                max_exercise_position = max(existing_exercise_positions) if existing_exercise_positions else -1
                new_exercise_position = getattr(ex_data, "position", max_exercise_position + 1)
                
                # Generate or use frontend-provided UID
                frontend_uid = getattr(ex_data, 'uid', None)
                exercise_uid = frontend_uid if frontend_uid else str(uuid4())
                print(f"[Backend] Creating new exercise - Frontend UID: {frontend_uid}, Using UID: {exercise_uid}")
                
                new_exercise = Exercise(
                    uid=exercise_uid,  # Use frontend UID or generate new
                    block_id=existing_block.id,
                    name=ex_data.name,
                    description=ex_data.description,
                    notes=ex_data.notes,
                    superset_id=ex_data.superset_id,
                    position=new_exercise_position,  # ✅ Position support
                )
                db.add(new_exercise)
                await db.flush()  # Get ID for sets
                
                # Create all sets for new exercise
                for set_data in ex_data.sets:
                    new_set = Set(
                        uid=set_data.uid if hasattr(set_data, 'uid') and set_data.uid else str(uuid4()),  # Use frontend UID or generate new
                        exercise_id=new_exercise.id,
                        weight=set_data.weight,
                        reps=set_data.reps,
                        duration=set_data.duration,
                        distance=set_data.distance,
                        rest_time=set_data.rest_time,
                        status=set_data.status,
                        completed_at=set_data.completed_at,
                        position=getattr(set_data, "position", 0)  # ✅ Position support
                    )
                    db.add(new_set)
                    
                    # No need for temp ID mapping anymore - we use UIDs
                    await db.flush()  # Ensure the set gets an ID
        
        # ✅ DELETE exercises that are no longer present (based on UIDs)
        for existing_exercise in existing_block.exercises:
            if existing_exercise.uid and existing_exercise.uid not in incoming_exercise_uids:
                print(f"[Backend] Deleting exercise with UID: {existing_exercise.uid} (not in incoming UIDs)")
                await db.delete(existing_exercise)
        
        await db.commit()
        
        # 🎉 Frisch gespeicherten Block laden und serialisieren!
        result_query = (
            select(Block)
            .options(selectinload(Block.exercises).selectinload(Exercise.sets))
            .where(Block.id == block_id)
        )
        result = await db.execute(result_query)
        saved_block = result.scalar_one()
        
        # Debug logging
        for ex in saved_block.exercises:
            print(f"[Backend] Exercise {ex.name} has {len(ex.sets)} sets")
            for s in ex.sets:
                print(f"[Backend]   - Set ID: {s.id}, UID: {s.uid}, Position: {s.position}")
        
        return BlockSaveResponse(
            block=BlockRead.model_validate(saved_block),
            temp_id_mappings={}  # Keep empty for backwards compatibility
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Error saving block: {str(e)}"
        )


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Kombinierte Security + Delete Query
    Löscht ein Workout samt aller abhängigen Objekte (Blocks, Exercises, Sets).
    """
    
    # ✅ SQLModel One-Liner: Direct workout query with security check
    workout = await db.scalar(
        select(Workout)
        .where(
            Workout.id == workout_id,
            Workout.user_id == UUID(current_user.id)  # ✅ Direct user security check!
        )
    )

    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found or access denied")
        
    try:
        await db.delete(workout)
        await db.commit()
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error deleting workout: {str(e)}")




@router.put("/sets/{set_id}/status", response_model=SetRead)
async def update_set_status_endpoint(
    set_id: int,
    payload: SetStatusUpdatePayload,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Kombinierte Security Query + Smart Field Updates
    """
    # ✅ SQLModel One-Liner: Direct set query with security check
    db_set = await db.scalar(
        select(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Set.id == set_id,
            Workout.user_id == UUID(current_user.id)  # ✅ Direct user security check!
        )
    )

    if not db_set:
        raise HTTPException(status_code=404, detail="Set not found or access denied")

    # ✅ Smart Field Updates - Pydantic validator macht datetime naive automatisch!
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(db_set, field, value)
    
    # set the completed_at timestamp to the current time
    db_set.completed_at = datetime.now(timezone.utc)

    try:
        await db.commit()
        await db.refresh(db_set)
        return SetRead.model_validate(db_set)  # ✅ Auto-Serialization!
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating set: {str(e)}")


# Schema for manual activity entry
class ManualActivitySchema(BaseModel):
    """
    Schema für manuelle Aktivitäts-Dokumentation
    Entspricht dem Frontend-Payload: name, description, timestamp
    """
    name: str = Field(..., min_length=1, max_length=200, description="Name der Aktivität")
    description: str = Field(..., min_length=1, max_length=1000, description="Beschreibung der Aktivität")
    timestamp: datetime | None = Field(default=None, description="Zeitpunkt der Aktivität (ISO string vom Frontend)")
    
    @field_validator('timestamp')
    @classmethod
    def make_datetime_naive(cls, v: datetime | None) -> datetime | None:
        """✅ Automatisch timezone-aware datetimes zu naive konvertieren"""
        if v is not None and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v
    
    @field_validator('name', 'description')
    @classmethod
    def strip_whitespace(cls, v: str) -> str:
        """✅ Whitespace entfernen und leere Strings abfangen"""
        if isinstance(v, str):
            v = v.strip()
            if not v:
                raise ValueError("Field cannot be empty")
        return v


@router.post("/manual-activity")
async def create_manual_activity(
    activity: ManualActivitySchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Einfache Workout-Erstellung mit Auto-Serialization
    """
    # ✅ SQLModel One-Liner: Get user with training plan
    user = await db.scalar(
        select(UserModel)
        .options(selectinload(UserModel.training_plan))
        .where(UserModel.id == UUID(current_user.id))
    )

    if not user or not user.training_plan:
        raise HTTPException(status_code=403, detail="User has no training plan")
    
    activity_time = activity.timestamp or datetime.utcnow()
    
    try:
        # ✅ Create workout with direct user_id relationship
        workout = Workout(
            user_id=UUID(current_user.id),  # ✅ Direct user relationship!
            training_plan_id=user.training_plan.id,  # Keep for context
            name=activity.name,
            description=activity.description,
            date_created=activity_time,
            duration=None,  # User didn't specify duration
            focus="Manual Activity",  # ✅ Default focus for manual activities
            notes=None  # No additional notes
        )
        db.add(workout)
        await db.flush()  # Get workout ID
        
        # ✅ CREATE BLOCK: Every workout needs at least one block
        block = Block(
            workout_id=workout.id,
            name="Manual Activity",
            description="Manually documented training activity",
            notes=None,
            position=0  # First and only block
        )
        db.add(block)
        await db.flush()  # Get block ID
        
        # ✅ CREATE EXERCISE: Block needs at least one exercise
        exercise = Exercise(
            block_id=block.id,
            name=activity.name,  # Use activity name as exercise name
            description=None,
            notes=activity.description,  # Put full description in notes
            superset_id=None,
            position=0  # First and only exercise
        )
        db.add(exercise)
        await db.flush()  # Get exercise ID
        
        # ✅ CREATE SET: Exercise needs at least one set (mark as completed)
        workout_set = Set(
            uid=str(uuid4()),  # Generate UID for manual activity set
            exercise_id=exercise.id,
            weight=None,  # No specific weight recorded
            reps=None,    # No specific reps recorded
            duration=None,  # No specific duration recorded
            distance=None,  # No specific distance recorded
            rest_time=None,  # No rest time for manual activity
            position=0,   # First and only set
            status=SetStatus.done,  # ✅ Mark as completed since it's historical
            completed_at=activity_time  # When the activity was done
        )
        db.add(workout_set)
        
        # ✅ Safe: Get workout_id while object is still attached to session
        workout_id = workout.id
        
        await db.commit()  # ✅ Commit all changes
        
        return {
            "success": True,
            "workout_id": workout_id
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error creating manual activity: {str(e)}")


