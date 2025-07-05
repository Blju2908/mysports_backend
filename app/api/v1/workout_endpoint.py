from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, case
from typing import List, Optional
from sqlalchemy.orm import selectinload
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from uuid import UUID

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus

from app.models.user_model import UserModel
from app.models.training_plan_model import TrainingPlan
from app.services.llm_logging_service import log_workout_revision, log_workout_revision_accept
from app.schemas.workout_schema import (
    WorkoutListRead,
    WorkoutWithBlocksRead,
    BlockRead,
    BlockInput,
    SetRead,
    SetUpdate,
    WorkoutStatusEnum
)
from app.llm.workout_revision.workout_revision_schemas import (
    WorkoutRevisionRequestSchema,
    WorkoutRevisionResponseSchema
)
from app.llm.workout_revision.workout_revision_service import run_workout_revision_chain
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema

from app.core.auth import get_current_user, User
from app.db.session import get_session


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
    response_model=BlockRead
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
    """
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
        
        # ✅ SMART ID-PRESERVING APPROACH: Update/Create/Delete based on comparison
        existing_exercises = {str(ex.id): ex for ex in existing_block.exercises}
        incoming_exercise_ids = set()
        
        # Process each incoming exercise
        for ex_data in block.exercises:
            if hasattr(ex_data, 'id') and ex_data.id and str(ex_data.id) in existing_exercises:
                # ✅ UPDATE existing exercise (preserves ID!)
                existing_exercise = existing_exercises[str(ex_data.id)]
                existing_exercise.name = ex_data.name
                existing_exercise.description = ex_data.description
                existing_exercise.notes = ex_data.notes
                existing_exercise.superset_id = ex_data.superset_id
                existing_exercise.position = getattr(ex_data, "position", existing_exercise.position or 0)  # ✅ Position support
                
                incoming_exercise_ids.add(str(ex_data.id))
                
                # ✅ SMART SET HANDLING: Update/Create/Delete sets
                existing_sets = {str(s.id): s for s in existing_exercise.sets}
                incoming_set_ids = set()
                
                for set_data in ex_data.sets:
                    if hasattr(set_data, 'id') and set_data.id and str(set_data.id) in existing_sets:
                        # ✅ UPDATE existing set (preserves ID!)
                        existing_set = existing_sets[str(set_data.id)]
                        existing_set.weight = set_data.weight
                        existing_set.reps = set_data.reps
                        existing_set.duration = set_data.duration
                        existing_set.distance = set_data.distance
                        existing_set.rest_time = set_data.rest_time
                        existing_set.status = set_data.status
                        existing_set.completed_at = set_data.completed_at
                        existing_set.position = getattr(set_data, "position", existing_set.position or 0)  # ✅ Position support
                        
                        incoming_set_ids.add(str(set_data.id))
                    else:
                        # ✅ CREATE new set (only if no valid ID or ID not found)
                        # Find max position and increment for new sets
                        existing_positions = [s.position or 0 for s in existing_exercise.sets if s.position is not None]
                        max_position = max(existing_positions) if existing_positions else -1
                        new_position = getattr(set_data, "position", max_position + 1)
                        
                        new_set = Set(
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
                
                # ✅ DELETE sets that are no longer present
                for set_id, existing_set in existing_sets.items():
                    if set_id not in incoming_set_ids:
                        await db.delete(existing_set)
                        
            else:
                # ✅ CREATE new exercise (only if no valid ID or ID not found)
                # Find max position and increment for new exercises
                existing_exercise_positions = [ex.position or 0 for ex in existing_block.exercises if ex.position is not None]
                max_exercise_position = max(existing_exercise_positions) if existing_exercise_positions else -1
                new_exercise_position = getattr(ex_data, "position", max_exercise_position + 1)
                
                new_exercise = Exercise(
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
        
        # ✅ DELETE exercises that are no longer present
        for ex_id, existing_exercise in existing_exercises.items():
            if ex_id not in incoming_exercise_ids:
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
        
        return BlockRead.model_validate(saved_block)
        
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
    
    # Special logic for done status
    if payload.status == SetStatus.done and not db_set.completed_at:
        db_set.completed_at = datetime.utcnow()
    elif payload.status != SetStatus.done:
        db_set.completed_at = None

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



@router.post("/{workout_id}/revise", response_model=WorkoutRevisionResponseSchema)
async def change_workout_endpoint(
    workout_id: int,
    request_data: WorkoutRevisionRequestSchema,
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Überarbeitet ein bestehendes Workout basierend auf User-Feedback.
    """
    # Prepare request data for logging
    request_log_data = {
        "workout_id": workout_id,
        "user_feedback": request_data.user_feedback,
        "has_training_plan": request_data.training_plan is not None,
        "has_training_history": request_data.training_history is not None and len(request_data.training_history) > 0
    }
    
    async with await log_workout_revision(
        db=db,
        user=current_user,
        workout_id=workout_id,
        request=request,
        request_data=request_log_data
    ) as call_logger:
        try:
            # ✅ SQLModel One-Liner: Direct workout query with security check
            workout_orm = await db.scalar(
                select(Workout)
                .where(
                    Workout.id == workout_id,
                    Workout.user_id == UUID(current_user.id)  # ✅ Direct user security check!
                )
            )
            
            if not workout_orm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Get user training_plan_id for logging
            user_query = select(UserModel).options(selectinload(UserModel.training_plan)).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            user = result.scalar_one_or_none()
            training_plan_id = user.training_plan.id if user and user.training_plan else None
            
            # Update training_plan_id für Logging
            if call_logger.log_entry and training_plan_id:
                call_logger.log_entry.training_plan_id = training_plan_id
            
            # Run the workout revision chain
            revised_workout_schema = await run_workout_revision_chain(
                workout_id=workout_id,
                user_feedback=request_data.user_feedback,
                user_id=UUID(current_user.id),
                training_plan=request_data.training_plan,
                training_history=request_data.training_history,
                db=db
            )
            
            # Create response
            response = WorkoutRevisionResponseSchema(
                original_workout_id=workout_id,
                user_feedback=request_data.user_feedback,
                revised_workout=revised_workout_schema,
                revision_timestamp=datetime.utcnow().isoformat()
            )
            
            # Log success
            await call_logger.log_success(
                http_status_code=200,
                response_summary=f"Workout revision completed for workout {workout_id}"
            )
            
            return response
            
        except HTTPException:
            # Log error wird automatisch durch den Context Manager gemacht
            raise
        except Exception as e:
            print(f"Error in change_workout_endpoint: {e}")
            import traceback
            traceback.print_exc()
            # Log error wird automatisch durch den Context Manager gemacht
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fehler bei der Workout-Überarbeitung"
            )


@router.post("/{workout_id}/revise/accept", response_model=WorkoutWithBlocksRead)
async def accept_revised_workout_endpoint(
    workout_id: int,
    revised_workout: WorkoutSchema,
    request: Request,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Akzeptiert ein überarbeitetes Workout und speichert es in der Datenbank.
    """
    # Prepare request data for logging
    request_log_data = {
        "workout_id": workout_id,
        "revised_workout_name": revised_workout.name,
        "revised_workout_description": revised_workout.description,
        "num_blocks": len(revised_workout.blocks) if revised_workout.blocks else 0
    }
    
    async with await log_workout_revision_accept(
        db=db,
        user=current_user,
        workout_id=workout_id,
        request=request,
        request_data=request_log_data
    ) as call_logger:
        try:
            # ✅ SQLModel One-Liner: Direct workout query with security check and eager loading
            workout_orm = await db.scalar(
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
            
            if not workout_orm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Get user training_plan_id for logging via relationship
            user_query = select(UserModel).options(selectinload(UserModel.training_plan)).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            user = result.scalar_one_or_none()
            training_plan_id = user.training_plan.id if user and user.training_plan else None
            
            # Update training_plan_id für Logging
            if call_logger.log_entry and training_plan_id:
                call_logger.log_entry.training_plan_id = training_plan_id
            
            # ✅ SIMPLIFIED: Save revised workout directly using SQLModel Best Practices
            # 1. Delete existing blocks (CASCADE deletes exercises + sets automatically)
            for block in workout_orm.blocks:
                await db.delete(block)
            await db.flush()
            
            # 2. Update workout details
            workout_orm.name = revised_workout.name
            workout_orm.description = revised_workout.description
            workout_orm.duration = revised_workout.duration
            workout_orm.focus = revised_workout.focus
            
            # 3. Create new blocks, exercises, sets (simple loops like in save_block!)
            for block_index, block_schema in enumerate(revised_workout.blocks):
                new_block = Block(
                    workout_id=workout_orm.id,
                    name=block_schema.name,
                    description=block_schema.description,
                    notes=getattr(block_schema, "notes", None),
                    position=getattr(block_schema, "position", block_index),  # ✅ Position support
                    is_amrap=getattr(block_schema, "is_amrap", False),
                    amrap_duration_minutes=getattr(block_schema, "amrap_duration_minutes", None)
                )
                db.add(new_block)
                await db.flush()  # Get block ID
                
                for exercise_index, exercise_schema in enumerate(block_schema.exercises):
                    new_exercise = Exercise(
                        block_id=new_block.id,
                        name=exercise_schema.name,
                        notes=getattr(exercise_schema, "notes", None),
                        superset_id=exercise_schema.superset_id,
                        position=getattr(exercise_schema, "position", exercise_index)  # ✅ Position support
                    )
                    db.add(new_exercise)
                    await db.flush()  # Get exercise ID
                    
                    for set_index, set_schema in enumerate(exercise_schema.sets):
                        # ✅ SIMPLIFIED: Parse values array [weight, reps, duration, distance, rest_time]
                        values = getattr(set_schema, 'values', [])
                        weight, reps, duration, distance, rest_time = (values + [None] * 5)[:5]  
                        
                        new_set = Set(
                            exercise_id=new_exercise.id,
                            weight=weight if isinstance(weight, (int, float)) else None,
                            reps=int(reps) if isinstance(reps, (int, float)) else None,
                            duration=int(duration) if isinstance(duration, (int, float)) else None,
                            distance=distance if isinstance(distance, (int, float)) else None,
                            rest_time=int(rest_time) if isinstance(rest_time, (int, float)) else None,
                            position=getattr(set_schema, "position", set_index),  # ✅ Position support
                            status=SetStatus.open  # All sets start as open
                        )
                        db.add(new_set)
            
            await db.commit()
            
            # ✅ FIXED: Re-load the workout with all relationships after commit
            workout_query_reload = (
                select(Workout)
                .options(
                    selectinload(Workout.blocks)
                    .selectinload(Block.exercises)
                    .selectinload(Exercise.sets)
                )
                .where(Workout.id == workout_id)
            )
            result = await db.execute(workout_query_reload)
            updated_workout = result.scalar_one()
            
            # ✅ SQLModel Magic: Auto-Serialization with properly loaded relationships
            result = WorkoutWithBlocksRead.model_validate(updated_workout)
            
            # Log success
            await call_logger.log_success(
                http_status_code=200,
                response_summary=f"Revised workout {workout_id} accepted and saved successfully"
            )
            
            # Return the updated workout
            return result
            
        except HTTPException:
            # Log error wird automatisch durch den Context Manager gemacht
            raise
        except Exception as e:
            print(f"Error in accept_revised_workout_endpoint: {e}")
            import traceback
            traceback.print_exc()
            # Log error wird automatisch durch den Context Manager gemacht
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Fehler beim Speichern des überarbeiteten Workouts"
            )
