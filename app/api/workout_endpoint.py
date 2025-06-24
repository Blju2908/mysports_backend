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
from app.models.workout_feedback_model import WorkoutFeedback
from app.models.user_model import UserModel
from app.services.workout_service import get_workout_details
from app.services.llm_logging_service import log_workout_revision, log_workout_revision_accept
from app.schemas.workout_schema import (
    WorkoutRead,
    WorkoutWithBlocksRead,
    BlockRead,
    BlockInput,
    ExerciseRead,
    SetRead
)
from app.llm.workout_revision.workout_revision_schemas import (
    WorkoutRevisionRequestSchema,
    WorkoutRevisionResponseSchema
)
from app.llm.workout_revision.workout_revision_service import run_workout_revision_chain, save_revised_workout
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.schemas.workout_feedback_schema import WorkoutFeedbackSchema, WorkoutFeedbackResponseSchema
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
    ✅ BEST PRACTICE: Kombinierte Security + Validation Query
    """
    # 🔥 OPTIMIERT: Eine Query für User + Block + Security Check!
    block_query = (
        select(Block)
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
        # 🎉 EXTREM EINFACH: Delete + Create statt komplexer Diffing!
        # SQLAlchemy löscht automatisch alle Exercises + Sets (CASCADE!)
        await db.delete(existing_block)
        await db.flush()  # Stelle sicher dass gelöscht wurde
        
        # Neuen Block erstellen (behält die gleiche ID)
        new_block = Block(
            id=block_id,  # Gleiche ID wiederverwenden
            workout_id=workout_id,
            name=block.name,
            description=block.description,
            notes=block.notes
        )
        db.add(new_block)
        await db.flush()  # ID für Relations
        
        # Exercises + Sets erstellen (einfache Loops statt Diffing!)
        for ex_data in block.exercises:
            new_exercise = Exercise(
                block_id=new_block.id,
                name=ex_data.name,
                description=ex_data.description,
                notes=ex_data.notes,
                superset_id=ex_data.superset_id
            )
            db.add(new_exercise)
            await db.flush()  # ID für Sets
            
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
        
        await db.commit()
        
        # 🎉 Frisch erstellten Block laden und automatisch serialisieren!
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

@router.post("/feedback", status_code=status.HTTP_201_CREATED, response_model=WorkoutFeedbackResponseSchema)
async def submit_workout_feedback(
    feedback: WorkoutFeedbackSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ BEST PRACTICE: Minimal CRUD mit automatischer Serialisierung
    """
    # 🔥 OPTIMIERT: Kombinierte Check für Duplicate + Workout Existenz!
    existing_query = (
        select(WorkoutFeedback)
        .join(Workout, WorkoutFeedback.workout_id == Workout.id)  # Prüft Workout Existenz
        .where(
            WorkoutFeedback.workout_id == feedback.workout_id,
            WorkoutFeedback.user_id == current_user.id
        )
    )
    result = await db.execute(existing_query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Feedback already exists")
    
    # Einfach erstellen + committen
    new_feedback = WorkoutFeedback(**feedback.model_dump(), user_id=current_user.id)
    db.add(new_feedback)
    
    try:
        await db.commit()
        await db.refresh(new_feedback)
        return WorkoutFeedbackResponseSchema.model_validate(new_feedback)  # ✅ Auto-Serialization!
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error saving feedback: {str(e)}")


@router.get("/feedback/{workout_id}", response_model=Optional[WorkoutFeedbackResponseSchema])
async def get_workout_feedback(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ SUPER EINFACH: Eine Query + Auto-Serialization!
    """
    # 🔥 OPTIMIERT: Eine Query für Feedback + Workout Existenz Check!
    feedback_query = (
        select(WorkoutFeedback)
        .join(Workout, WorkoutFeedback.workout_id == Workout.id)  # Prüft Workout Existenz
        .where(
            WorkoutFeedback.workout_id == workout_id,
            WorkoutFeedback.user_id == current_user.id
        )
    )
    result = await db.execute(feedback_query)
    feedback = result.scalar_one_or_none()
    
    return WorkoutFeedbackResponseSchema.model_validate(feedback) if feedback else None


@router.put("/feedback/{feedback_id}", response_model=WorkoutFeedbackResponseSchema)
async def update_workout_feedback(
    feedback_id: int,
    updated_feedback: WorkoutFeedbackSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ CLEAN UPDATE: Security + Auto-Serialization!
    """
    # 🔥 OPTIMIERT: Eine Query für Feedback + Security + Workout Existenz!
    feedback_query = (
        select(WorkoutFeedback)
        .join(Workout, WorkoutFeedback.workout_id == Workout.id)  # Prüft Workout Existenz
        .where(
            WorkoutFeedback.id == feedback_id,
            WorkoutFeedback.user_id == current_user.id,  # Security
            Workout.id == updated_feedback.workout_id  # Workout muss existieren
        )
    )
    result = await db.execute(feedback_query)
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback not found or access denied")
    
    # Update fields
    for field, value in updated_feedback.model_dump(exclude_unset=True).items():
        setattr(feedback, field, value)
    
    try:
        await db.commit()
        await db.refresh(feedback)
        return WorkoutFeedbackResponseSchema.model_validate(feedback)  # ✅ Auto-Serialization!
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating feedback: {str(e)}")


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
            # Verify user has access to this workout
            workout_orm = await get_workout_details(workout_id=workout_id, db=db)
            
            user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if (not user or not user.training_plan_id or 
                workout_orm.training_plan_id != user.training_plan_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Update training_plan_id für Logging
            if call_logger.log_entry:
                call_logger.log_entry.training_plan_id = user.training_plan_id
            
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
            # Verify user has access to this workout
            workout_orm = await get_workout_details(workout_id=workout_id, db=db)
            
            user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
            result = await db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if (not user or not user.training_plan_id or 
                workout_orm.training_plan_id != user.training_plan_id):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Keine Berechtigung für den Zugriff auf dieses Workout"
                )
            
            # Update training_plan_id für Logging
            if call_logger.log_entry:
                call_logger.log_entry.training_plan_id = user.training_plan_id
            
            # Save the revised workout to the database
            updated_workout = await save_revised_workout(
                workout_id=workout_id,
                revised_workout_schema=revised_workout,
                db=db
            )
            
            
            # Build response data
            response_blocks_data = []
            for block_orm in updated_workout.blocks:
                response_exercises_data = []
                for exercise_orm in block_orm.exercises:
                    response_sets_data = [SetRead.model_validate(s) for s in exercise_orm.sets]
                    response_exercises_data.append(
                        ExerciseRead(
                            id=exercise_orm.id,
                            name=exercise_orm.name,
                            description=exercise_orm.description,
                            notes=exercise_orm.notes,
                            superset_id=exercise_orm.superset_id,
                            block_id=exercise_orm.block_id,
                            sets=response_sets_data
                        )
                    )
                response_blocks_data.append(
                    BlockRead(
                        id=block_orm.id,
                        name=block_orm.name,
                        description=block_orm.description,
                        notes=block_orm.notes,
                        workout_id=block_orm.workout_id,
                        exercises=response_exercises_data
                    )
                )
            
            result = WorkoutWithBlocksRead(
                id=updated_workout.id,
                training_plan_id=updated_workout.training_plan_id,
                name=updated_workout.name,
                date_created=updated_workout.date_created,
                description=updated_workout.description,
                duration=updated_workout.duration,
                focus=updated_workout.focus,
                notes=updated_workout.notes,
                status=updated_workout.status,
                blocks=response_blocks_data
            )
            
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
