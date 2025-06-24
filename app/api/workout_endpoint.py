from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select 
from typing import List, Optional
from sqlalchemy.orm import selectinload
from datetime import datetime
from pydantic import BaseModel, field_validator
from uuid import UUID

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus

from app.models.user_model import UserModel
from app.services.llm_logging_service import log_workout_revision, log_workout_revision_accept
from app.schemas.workout_schema import (
    WorkoutRead,
    WorkoutWithBlocksRead,
    BlockRead,
    BlockInput,
    SetRead
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
    completed_at: Optional[datetime] = None
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    notes: Optional[str] = None
    
    @field_validator('completed_at')
    @classmethod
    def make_datetime_naive(cls, v: Optional[datetime]) -> Optional[datetime]:
        """✅ Automatisch timezone-aware datetimes zu naive konvertieren"""
        if v is not None and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

router = APIRouter(tags=["workouts"])



@router.get("/", response_model=List[WorkoutRead])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):

    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        return []

    # Einfache Query mit Relations laden
    workout_query = (
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(Workout.training_plan_id == user.training_plan_id)
        .order_by(Workout.date_created.desc())
    )

    result = await db.execute(workout_query)
    workouts = result.scalars().all()

    return [WorkoutRead.model_validate(w) for w in workouts]


@router.get("/{workout_id}", response_model=WorkoutWithBlocksRead)
async def get_workout_detail(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Direkte DB-Query im Endpoint + automatische Sortierung im Model
    """
    
    # User-Check
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user or not user.training_plan_id:
        raise HTTPException(status_code=403, detail="User has no training plan")
    
    # Workout laden - direkt mit Security-Check in der Query!
    workout_query = (
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(
            Workout.id == workout_id,
            Workout.training_plan_id == user.training_plan_id  # 🔒 Security direkt in Query!
        )
    )
    
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    
    # ✅ WICHTIG: Nutze die sortierte get_sorted_blocks() Methode!
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
    ✅ SUPER EINFACH: SQLModel Best Practice - Security + Auto-Serialization!
    """
    # User-Check
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        raise HTTPException(status_code=403, detail="User has no training plan")

    # Block laden mit Security direkt in Query! 🔒
    block_query = (
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            Workout.training_plan_id == user.training_plan_id,  # Security!
        )
    )

    result = await db.execute(block_query)
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(status_code=404, detail="Block not found")

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
    # 🔥 OPTIMIERT: Eine Query für User + Block + Security Check mit eager loading!
    block_query = (
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)  # User muss training plan haben
        )
    )
    result = await db.execute(block_query)
    existing_block = result.scalar_one_or_none()
    
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
                        
                        incoming_set_ids.add(str(set_data.id))
                    else:
                        # ✅ CREATE new set (only if no valid ID or ID not found)
                        new_set = Set(
                            exercise_id=existing_exercise.id,
                            weight=set_data.weight,
                            reps=set_data.reps,
                            duration=set_data.duration,
                            distance=set_data.distance,
                            rest_time=set_data.rest_time,
                            status=set_data.status,
                            completed_at=set_data.completed_at
                        )
                        db.add(new_set)
                
                # ✅ DELETE sets that are no longer present
                for set_id, existing_set in existing_sets.items():
                    if set_id not in incoming_set_ids:
                        await db.delete(existing_set)
                        
            else:
                # ✅ CREATE new exercise (only if no valid ID or ID not found)
                new_exercise = Exercise(
                    block_id=existing_block.id,
                    name=ex_data.name,
                    description=ex_data.description,
                    notes=ex_data.notes,
                    superset_id=ex_data.superset_id
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
                        completed_at=set_data.completed_at
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
    
    # 🔥 OPTIMIERT: Eine Query für User + Workout + Security Check!
    workout_query = (
        select(Workout)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            Workout.id == workout_id,
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)  # User muss training plan haben
        )
    )
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()

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
    set_query = (
        select(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
        .where(
            Set.id == set_id,
            UserModel.id == UUID(current_user.id),
            UserModel.training_plan_id.is_not(None)  # User muss training plan haben
        )
    )
    result = await db.execute(set_query)
    db_set = result.scalar_one_or_none()

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
    name: str
    description: str
    timestamp: Optional[datetime] = None
    
    @field_validator('timestamp')
    @classmethod
    def make_datetime_naive(cls, v: Optional[datetime]) -> Optional[datetime]:
        """✅ Automatisch timezone-aware datetimes zu naive konvertieren"""
        if v is not None and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v


@router.post("/manual-activity", response_model=WorkoutRead)
async def create_manual_activity(
    activity: ManualActivitySchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Einfache Workout-Erstellung mit Auto-Serialization
    """
    # User validation - könnte auch in Combined Query, aber hier ist separate OK da wir training_plan_id brauchen
    user_query = select(UserModel).where(
        UserModel.id == UUID(current_user.id),
        UserModel.training_plan_id.is_not(None)
    )
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=403, detail="User has no training plan")
    
    activity_time = activity.timestamp or datetime.utcnow()
    
    try:
        # ✅ Simplified: Create all objects in sequence
        workout = Workout(
            training_plan_id=user.training_plan_id,
            name=activity.name,
            description=activity.description,
            date_created=activity_time,
        )
        db.add(workout)
        await db.flush()
        
        block = Block(
            workout_id=workout.id,
            name="Manual Activity",
            description="Manually logged activity",
        )
        db.add(block)
        await db.flush()
        
        exercise = Exercise(
            block_id=block.id,
            name=activity.name,
            notes=activity.description,
        )
        db.add(exercise)
        await db.flush()
        
        # ✅ Minimal set - only required fields
        workout_set = Set(
            exercise_id=exercise.id,
            status=SetStatus.done,
            completed_at=activity_time,
        )
        db.add(workout_set)
        
        await db.commit()
        await db.refresh(workout)
        return WorkoutRead.model_validate(workout)  # ✅ Auto-Serialization!
        
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
            # ✅ OPTIMIZED: Combined Security Query (wie im accept endpoint!)
            workout_query = (
                select(Workout)
                .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
                .where(
                    Workout.id == workout_id,
                    UserModel.id == UUID(current_user.id),
                    UserModel.training_plan_id.is_not(None)
                )
            )
            result = await db.execute(workout_query)
            workout_orm = result.scalar_one_or_none()
            
            if not workout_orm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Get user training_plan_id for logging
            user_query = select(UserModel.training_plan_id).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            training_plan_id = result.scalar_one_or_none()
            
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
            # ✅ OPTIMIZED: Combined Security + Workout Load Query (wie in anderen Endpoints!)
            workout_query = (
                select(Workout)
                .options(
                    selectinload(Workout.blocks)
                    .selectinload(Block.exercises)
                    .selectinload(Exercise.sets)
                )
                .join(UserModel, Workout.training_plan_id == UserModel.training_plan_id)
                .where(
                    Workout.id == workout_id,
                    UserModel.id == UUID(current_user.id),
                    UserModel.training_plan_id.is_not(None)
                )
            )
            result = await db.execute(workout_query)
            workout_orm = result.scalar_one_or_none()
            
            if not workout_orm:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Get user training_plan_id for logging
            user_query = select(UserModel.training_plan_id).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            training_plan_id = result.scalar_one_or_none()
            
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
            for block_schema in revised_workout.blocks:
                new_block = Block(
                    workout_id=workout_orm.id,
                    name=block_schema.name,
                    description=block_schema.description,
                    notes=getattr(block_schema, "notes", None),
                    is_amrap=getattr(block_schema, "is_amrap", False),
                    amrap_duration_minutes=getattr(block_schema, "amrap_duration_minutes", None)
                )
                db.add(new_block)
                await db.flush()  # Get block ID
                
                for exercise_schema in block_schema.exercises:
                    new_exercise = Exercise(
                        block_id=new_block.id,
                        name=exercise_schema.name,
                        notes=getattr(exercise_schema, "notes", None),
                        superset_id=exercise_schema.superset_id
                    )
                    db.add(new_exercise)
                    await db.flush()  # Get exercise ID
                    
                    for set_schema in exercise_schema.sets:
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
