from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join, update, delete, func, case, and_
from typing import List, Optional, Union, Dict, Any
from sqlalchemy.orm import selectinload
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from app.models.workout_feedback_model import WorkoutFeedback
from app.models.user_model import UserModel
from app.services.workout_service import get_workout_details
from app.services.llm_logging_service import log_workout_revision, log_workout_revision_accept
from app.llm.schemas.workout_schema import (
    WorkoutResponseSchema,
    WorkoutSchemaWithBlocks,
    BlockResponseSchema,
    ExerciseResponseSchema,
    SetResponseSchema,
    WorkoutStatusEnum,
    BlockSchema
)
from app.schemas.workout_schema import WorkoutResponseSchema as OptimizedWorkoutResponseSchema
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

# Schema for individual set data when saving block activity (includes set_id)
class SetExecutionInputSchema(SetStatusUpdatePayload): # Inherits fields from SetStatusUpdatePayload
    set_id: int

# Payload for saving activity for multiple sets within a block
class BlockActivityPayload(BaseModel):
    block_id: int 
    workout_id: int 
    sets: List[SetExecutionInputSchema] # Uses SetExecutionInputSchema which includes set_id

class ResetBlocksPayload(BaseModel): # Moved from inline for clarity
    block_ids: list[int]

router = APIRouter(tags=["workouts"])

def calculate_workout_status(workout_orm: Workout) -> WorkoutStatusEnum:
    if not workout_orm.blocks:
        return WorkoutStatusEnum.NOT_STARTED

    all_sets = []
    for block in workout_orm.blocks:
        for exercise in block.exercises:
            all_sets.extend(exercise.sets)

    if not all_sets:
        return WorkoutStatusEnum.NOT_STARTED

    num_done_sets = sum(1 for s in all_sets if s.status == SetStatus.done)

    if num_done_sets == len(all_sets):
        return WorkoutStatusEnum.DONE
    elif num_done_sets > 0 or any(s.status == SetStatus.open for s in all_sets): # Simplified: if any progress or any open sets (and not all done)
        # More precise: if num_done_sets > 0, it's definitely STARTED.
        # If num_done_sets == 0 but there are sets (implicitly all OPEN), it's NOT_STARTED.
        # Let's refine: if any set is 'done', it's 'started'. If no sets are 'done' but sets exist (all 'open'), it's 'not_started'.
        if num_done_sets > 0:
             return WorkoutStatusEnum.STARTED
        else: # No sets are 'done', all existing sets must be 'open'
             return WorkoutStatusEnum.NOT_STARTED
    
    return WorkoutStatusEnum.NOT_STARTED # Default/fallback if no sets or unexpected state


async def calculate_workout_statuses_optimized(
    workout_ids: List[int], 
    db: AsyncSession
) -> Dict[int, WorkoutStatusEnum]:
    """
    ✅ OPTIMIZED: Calculate workout status for multiple workouts with single SQL query
    
    This replaces multiple individual status calculations with one efficient query.
    React Query V5 Best Practice: Minimize database round trips.
    """
    if not workout_ids:
        return {}
    
    # ✅ SINGLE SQL QUERY: Calculate status for all workouts at once
    status_query = (
        select(
            Workout.id.label('workout_id'),
            func.count(Set.id).label('total_sets'),
            func.sum(
                case(
                    (Set.status == SetStatus.done, 1), 
                    else_=0
                )
            ).label('completed_sets')
        )
        .select_from(Workout)
        .outerjoin(Block, Block.workout_id == Workout.id)
        .outerjoin(Exercise, Exercise.block_id == Block.id)
        .outerjoin(Set, Set.exercise_id == Exercise.id)
        .where(Workout.id.in_(workout_ids))
        .group_by(Workout.id)
    )
    
    result = await db.execute(status_query)
    status_data = result.all()
    
    # ✅ EFFICIENT: Convert to status enum in Python
    workout_statuses = {}
    for row in status_data:
        workout_id = row.workout_id
        total_sets = row.total_sets or 0
        completed_sets = row.completed_sets or 0
        
        if total_sets == 0:
            status = WorkoutStatusEnum.NOT_STARTED
        elif completed_sets == total_sets:
            status = WorkoutStatusEnum.DONE
        elif completed_sets > 0:
            status = WorkoutStatusEnum.STARTED
        else:
            status = WorkoutStatusEnum.NOT_STARTED
            
        workout_statuses[workout_id] = status
    
    # ✅ HANDLE: Workouts not in result (no sets) - default to NOT_STARTED
    for workout_id in workout_ids:
        if workout_id not in workout_statuses:
            workout_statuses[workout_id] = WorkoutStatusEnum.NOT_STARTED
    
    return workout_statuses


@router.get("/", response_model=List[OptimizedWorkoutResponseSchema])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ OPTIMIZED: Get all workouts with computed status in a single efficient call.
    
    Performance improvements:
    - Single SQL query for status calculation
    - No more 4x duplicate calls from frontend
    - Status included directly in response
    - Supports React Query V5 cache invalidation patterns
    """
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        return []

    # ✅ LIGHTWEIGHT: Get workout metadata only (no joins)
    workout_query = (
        select(Workout)
        .where(Workout.training_plan_id == user.training_plan_id)
        .order_by(Workout.date_created.desc())
    )

    result = await db.execute(workout_query)
    workouts_orm = result.scalars().all()
    
    if not workouts_orm:
        return []

    # ✅ BATCH STATUS CALCULATION: Single query for all workout statuses
    workout_ids = [w.id for w in workouts_orm]
    workout_statuses = await calculate_workout_statuses_optimized(workout_ids, db)

    # ✅ EFFICIENT: Build response with pre-calculated statuses
    response_workouts = []
    for workout_orm_item in workouts_orm:
        status = workout_statuses.get(workout_orm_item.id, WorkoutStatusEnum.NOT_STARTED)
        response_workout = OptimizedWorkoutResponseSchema(
            id=workout_orm_item.id,
            training_plan_id=workout_orm_item.training_plan_id,
            name=workout_orm_item.name,
            date_created=workout_orm_item.date_created,
            description=workout_orm_item.description,
            duration=workout_orm_item.duration,
            focus=workout_orm_item.focus,
            notes=workout_orm_item.notes,
            status=status,  # ✅ STATUS INCLUDED: No frontend computation needed!
        )
        response_workouts.append(response_workout)

    return response_workouts


@router.get("/{workout_id}", response_model=WorkoutSchemaWithBlocks)
async def get_workout_detail(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    ✅ OPTIMIZED: Get detailed workout information with efficient status calculation.
    
    Uses the same optimized status calculation as the list endpoint for consistency.
    """
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
    
    # ✅ CONSISTENT: Use same optimized status calculation as list endpoint
    workout_statuses = await calculate_workout_statuses_optimized([workout_id], db)
    calculated_status = workout_statuses.get(workout_id, WorkoutStatusEnum.NOT_STARTED)

    # Explicitly construct the response data if direct ORM to Pydantic conversion is problematic
    # or if sub-models need specific handling.
    response_blocks_data = []
    for block_orm in workout_orm.blocks:
        response_exercises_data = []
        for exercise_orm in block_orm.exercises:
            response_sets_data = [SetResponseSchema.from_orm(s) for s in exercise_orm.sets]
            response_exercises_data.append(
                ExerciseResponseSchema(
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
            BlockResponseSchema(
                id=block_orm.id,
                name=block_orm.name,
                description=block_orm.description,
                notes=block_orm.notes,
                workout_id=block_orm.workout_id,
                exercises=response_exercises_data
            )
        )

    # Construct the final response using the Pydantic model
    return WorkoutSchemaWithBlocks(
        id=workout_orm.id,
        training_plan_id=workout_orm.training_plan_id,
        name=workout_orm.name,
        date_created=workout_orm.date_created,
        description=workout_orm.description,
        duration=workout_orm.duration,
        focus=workout_orm.focus,
        notes=workout_orm.notes,
        status=calculated_status,
        blocks=response_blocks_data
    )


@router.get("/{workout_id}/blocks/{block_id}", response_model=BlockResponseSchema)
async def get_block_detail(
    workout_id: int,
    block_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific block including all exercises and sets.
    Ensures the block belongs to a workout the user has access to.
    """
    # 1. Prüfen, ob der User Zugriff auf das Workout hat
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no training plan",
        )

    # 2. Den spezifischen Block holen und sicherstellen, dass er zum richtigen Workout gehört,
    #    auf das der User Zugriff hat. Lade Übungen und Sets.
    block_query = (
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            Workout.training_plan_id == user.training_plan_id,
        )
    )

    result = await db.execute(block_query)
    block = result.scalar_one_or_none()

    if not block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found or user does not have access to the parent workout",
        )

    # Build response using BlockResponseSchema
    response_exercises_data = []
    for exercise_orm in block.exercises:
        response_sets_data = [SetResponseSchema.from_orm(s) for s in exercise_orm.sets]
        response_exercises_data.append(
            ExerciseResponseSchema(
                id=exercise_orm.id,
                name=exercise_orm.name,
                description=exercise_orm.description,
                notes=exercise_orm.notes,
                superset_id=exercise_orm.superset_id,
                block_id=exercise_orm.block_id,
                sets=response_sets_data
            )
        )
    return BlockResponseSchema(
        id=block.id,
        name=block.name,
        description=block.description,
        notes=block.notes,
        workout_id=block.workout_id,
        exercises=response_exercises_data
    )


@router.post(
    "/{workout_id}/blocks/{block_id}",
    response_model=BlockSchema
)
async def save_block(
    workout_id: int,
    block_id: int,
    block: BlockSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Speichert einen kompletten Block (inkl. Exercises und Sets) und übernimmt das Diffing.
    """
    # 1. Lade aktuellen Block inkl. Exercises & Sets
    db_block_query = (
        select(Block)
        .options(selectinload(Block.exercises).selectinload(Exercise.sets))
        .join(Workout, Block.workout_id == Workout.id)
        .where(Block.id == block_id, Workout.id == workout_id)
    )
    db_block_result = await db.execute(db_block_query)
    db_block = db_block_result.scalar_one_or_none()
    if not db_block:
        raise HTTPException(status_code=404, detail="Block nicht gefunden")

    # Hilfsfunktionen für schnellen Zugriff
    def get_exercise_map(exercises):
        return {ex.id: ex for ex in exercises}
    def get_set_map(sets):
        return {s.id: s for s in sets}

    # 2. Diffing: Exercises
    db_exercise_map = get_exercise_map(db_block.exercises)
    payload_exercise_map = get_exercise_map(block.exercises)

    # 2a. Delete Exercises (in DB, aber nicht mehr im Payload)
    for db_ex in db_block.exercises:
        if db_ex.id not in payload_exercise_map:
            await db.delete(db_ex)

    # 2b. Add/Update Exercises
    for ex in block.exercises:
        if isinstance(ex.id, str) or ex.id is None:
            # Neu: Exercise anlegen
            new_ex = Exercise(
                name=ex.name,
                description=ex.description,
                notes=ex.notes,
                superset_id=ex.superset_id,
                block_id=block_id
            )
            db.add(new_ex)
            await db.flush()  # ID für Sets
            db_ex_id = new_ex.id
        else:
            # Update: Exercise updaten
            db_ex = db_exercise_map.get(ex.id)
            if db_ex:
                db_ex.name = ex.name
                db_ex.description = ex.description
                db_ex.notes = ex.notes
                db_ex.superset_id = ex.superset_id
                db.add(db_ex)
                db_ex_id = db_ex.id
            else:
                continue  # Sollte nicht passieren

        # 3. Diffing: Sets für diese Exercise
        # Hole aktuelle Sets aus DB (nach dem Anlegen ggf. leer)
        if isinstance(ex.id, str) or ex.id is None:
            db_sets = []
        else:
            db_sets = db_exercise_map[ex.id].sets if ex.id in db_exercise_map else []
        db_set_map = get_set_map(db_sets)
        payload_set_map = get_set_map(ex.sets)

        # 3a. Delete Sets
        for db_set in db_sets:
            if db_set.id not in payload_set_map:
                await db.delete(db_set)

        # 3b. Add/Update Sets
        for s in ex.sets:
            if isinstance(s.id, str) or s.id is None:
                # Neu: Set anlegen
                new_set = Set(
                    exercise_id=db_ex_id,
                    reps=s.reps,
                    weight=s.weight,
                    duration=s.duration,
                    distance=s.distance,
                    rest_time=s.rest_time,
                    status=s.status,
                    completed_at=make_naive(s.completed_at) if s.completed_at else None,
                )
                db.add(new_set)
            else:
                # Update: Set updaten
                db_set = db_set_map.get(s.id)
                if db_set:
                    db_set.reps = s.reps
                    db_set.weight = s.weight
                    db_set.duration = s.duration
                    db_set.distance = s.distance
                    db_set.rest_time = s.rest_time
                    db_set.status = s.status
                    db_set.completed_at = make_naive(s.completed_at) if s.completed_at else None
                    db.add(db_set)

    await db.commit()

    # Lade den aktualisierten Block erneut
    db_block_result = await db.execute(db_block_query)
    db_block = db_block_result.scalar_one_or_none()

    # Baue das Response-Objekt
    def orm_to_schema_block(db_block):
        return BlockSchema(
            id=db_block.id,
            workout_id=db_block.workout_id,
            name=db_block.name,
            description=db_block.description,
            notes=db_block.notes,
            exercises=[
                dict(
                    id=ex.id,
                    name=ex.name,
                    description=ex.description,
                    notes=ex.notes,
                    superset_id=ex.superset_id,
                    sets=[
                        dict(
                            id=s.id,
                            reps=s.reps,
                            weight=s.weight,
                            duration=s.duration,
                            distance=s.distance,
                            rest_time=s.rest_time,
                            status=s.status,
                            completed_at=s.completed_at
                        ) for s in ex.sets
                    ]
                ) for ex in db_block.exercises
            ]
        )
    return orm_to_schema_block(db_block)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Löscht ein Workout samt aller abhängigen Objekte (Blocks, Exercises, Sets).
    Die Trainingshistorie bleibt erhalten, nur die set_id wird automatisch auf NULL gesetzt.
    """
    
    # Prüfe, ob das Workout existiert und zum User gehört
    user_db_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    user_res = await db.execute(user_db_query)
    user_db = user_res.scalar_one_or_none()

    if not user_db or not user_db.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User has no training plan."
        )

    workout_query = select(Workout).where(
        Workout.id == workout_id, Workout.training_plan_id == user_db.training_plan_id
    )
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=404, detail="Workout nicht gefunden oder kein Zugriff."
        )
        
    try:
        await db.delete(workout)
        await db.commit()
        return None
    except Exception as e:
        await db.rollback()
        print(f"Error deleting workout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Löschen des Workouts."
        )

@router.post("/feedback", status_code=status.HTTP_201_CREATED, response_model=WorkoutFeedbackResponseSchema)
async def submit_workout_feedback(
    feedback: WorkoutFeedbackSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Speichert neues Feedback zu einem Workout
    """
    # Prüfen ob das Workout existiert und User Zugriff hat
    workout_query = select(Workout).where(Workout.id == feedback.workout_id)
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout nicht gefunden")
    
    # Prüfen ob User bereits Feedback abgegeben hat (optional)
    existing_feedback_query = select(WorkoutFeedback).where(
        WorkoutFeedback.workout_id == feedback.workout_id,
        WorkoutFeedback.user_id == current_user.id
    )
    result = await db.execute(existing_feedback_query)
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Du hast bereits Feedback zu diesem Workout abgegeben")
    
    # Feedback erstellen
    new_feedback = WorkoutFeedback(
        workout_id=feedback.workout_id,
        user_id=current_user.id,
        rating=feedback.rating,
        duration_rating=feedback.duration_rating,
        intensity_rating=feedback.intensity_rating,
        comment=feedback.comment
    )
    
    db.add(new_feedback)
    
    try:
        await db.commit()
        await db.refresh(new_feedback)
        
        # UUID zu String konvertieren, um Serialisierungsfehler zu vermeiden
        response_data = {
            "id": new_feedback.id,
            "workout_id": new_feedback.workout_id,
            "user_id": str(new_feedback.user_id),  # UUID zu String konvertieren
            "rating": new_feedback.rating,
            "duration_rating": new_feedback.duration_rating,
            "intensity_rating": new_feedback.intensity_rating,
            "comment": new_feedback.comment,
            "created_at": new_feedback.created_at
        }
        
        return response_data
    except Exception as e:
        await db.rollback()
        print(f"Error submitting feedback: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Speichern des Feedbacks")


@router.get("/feedback/{workout_id}", response_model=Optional[WorkoutFeedbackResponseSchema])
async def get_workout_feedback(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Holt das Feedback eines Users zu einem bestimmten Workout.
    Gibt null zurück wenn kein Feedback vorhanden ist (normales Verhalten).
    """
    # Prüfen ob das Workout existiert
    workout_query = select(Workout).where(Workout.id == workout_id)
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout nicht gefunden")
    
    # Feedback des Users abrufen
    feedback_query = select(WorkoutFeedback).where(
        WorkoutFeedback.workout_id == workout_id,
        WorkoutFeedback.user_id == current_user.id
    )
    result = await db.execute(feedback_query)
    feedback = result.scalar_one_or_none()
    
    # Kein Feedback ist normales Verhalten - return null instead of 404
    if not feedback:
        return None
    
    # UUID zu String konvertieren
    response_data = {
        "id": feedback.id,
        "workout_id": feedback.workout_id,
        "user_id": str(feedback.user_id),
        "rating": feedback.rating,
        "duration_rating": feedback.duration_rating,
        "intensity_rating": feedback.intensity_rating,
        "comment": feedback.comment,
        "created_at": feedback.created_at
    }
    
    return response_data


@router.put("/feedback/{feedback_id}", response_model=WorkoutFeedbackResponseSchema)
async def update_workout_feedback(
    feedback_id: int,
    updated_feedback: WorkoutFeedbackSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Aktualisiert ein bestehendes Feedback
    """
    # Prüfen ob das Feedback existiert und dem User gehört
    feedback_query = select(WorkoutFeedback).where(
        WorkoutFeedback.id == feedback_id,
        WorkoutFeedback.user_id == current_user.id
    )
    result = await db.execute(feedback_query)
    feedback = result.scalar_one_or_none()
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Feedback nicht gefunden oder keine Berechtigung")
    
    # Prüfen ob das Workout existiert
    workout_query = select(Workout).where(Workout.id == updated_feedback.workout_id)
    result = await db.execute(workout_query)
    workout = result.scalar_one_or_none()
    
    if not workout:
        raise HTTPException(status_code=404, detail="Workout nicht gefunden")
    
    # Feedback aktualisieren
    feedback.rating = updated_feedback.rating
    feedback.duration_rating = updated_feedback.duration_rating
    feedback.intensity_rating = updated_feedback.intensity_rating
    feedback.comment = updated_feedback.comment
    
    db.add(feedback)
    
    try:
        await db.commit()
        await db.refresh(feedback)
        
        # UUID zu String konvertieren
        response_data = {
            "id": feedback.id,
            "workout_id": feedback.workout_id,
            "user_id": str(feedback.user_id),
            "rating": feedback.rating,
            "duration_rating": feedback.duration_rating,
            "intensity_rating": feedback.intensity_rating,
            "comment": feedback.comment,
            "created_at": feedback.created_at
        }
        
        return response_data
    except Exception as e:
        await db.rollback()
        print(f"Error updating feedback: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Aktualisieren des Feedbacks")


@router.put("/sets/{set_id}/status", response_model=SetResponseSchema)
async def update_set_status_endpoint(
    set_id: int,
    payload: SetStatusUpdatePayload,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Updates the status and execution details of a specific set.
    Ensures the set belongs to the current user's training plan.
    """
    user_db_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    user_res = await db.execute(user_db_query)
    user_db = user_res.scalar_one_or_none()

    if not user_db or not user_db.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="User has no training plan."
        )

    # Fetch the set and verify ownership via training plan
    set_query = (
        select(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Set.id == set_id,
            Workout.training_plan_id == user_db.training_plan_id
        )
    )
    set_result = await db.execute(set_query)
    db_set = set_result.scalar_one_or_none()

    if not db_set:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Set not found or user does not have access.",
        )

    # Update fields from payload
    db_set.status = payload.status
    if payload.status == SetStatus.done:
        db_set.completed_at = make_naive(payload.completed_at) if payload.completed_at else datetime.utcnow()
    else:
        db_set.completed_at = None # Clear if not 'done'

    if payload.weight is not None:
        db_set.weight = payload.weight
    if payload.reps is not None:
        db_set.reps = payload.reps
    if payload.duration is not None:
        db_set.duration = payload.duration
    if payload.distance is not None:
        db_set.distance = payload.distance
    if payload.notes is not None: # Allow updating notes
        db_set.notes = payload.notes

    db.add(db_set)
    try:
        await db.commit()
        await db.refresh(db_set)
    except Exception as e:
        await db.rollback()
        print(f"Error updating set status for set_id {set_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update status for set {set_id}.",
        )
    return db_set


# Schema for manual activity entry
class ManualActivitySchema(BaseModel):
    name: str
    description: str
    timestamp: Optional[datetime] = None


@router.post("/manual-activity", response_model=WorkoutResponseSchema)
async def create_manual_activity(
    activity: ManualActivitySchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Creates a simple workout from a manual activity entry.
    Creates one block, one exercise, and one completed set with the activity information.
    """
    # Validate user and get training plan
    user_db_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    user_res = await db.execute(user_db_query)
    user_db = user_res.scalar_one_or_none()

    if not user_db or not user_db.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="User has no training plan"
        )
    
    # Use provided timestamp or current time
    activity_time = activity.timestamp or datetime.utcnow()
    
    try:
        # 1. Create the workout
        new_workout = Workout(
            training_plan_id=user_db.training_plan_id,
            name=activity.name,
            description=activity.description,
            date_created=activity_time,
        )
        db.add(new_workout)
        await db.flush()  # Get ID for relationships
        
        # 2. Create the block
        new_block = Block(
            workout_id=new_workout.id,
            name="Block 1",
            description="Manuell dokumentierte Aktivität",
        )
        db.add(new_block)
        await db.flush()  # Get ID for relationships
        
        # 3. Create the exercise
        new_exercise = Exercise(
            block_id=new_block.id,
            name=activity.name,
            notes=activity.description,
        )
        db.add(new_exercise)
        await db.flush()  # Get ID for relationships
        
        # 4. Create the set
        new_set = Set(
            exercise_id=new_exercise.id,
            status=SetStatus.done,
            completed_at=activity_time,
            reps=0,
            weight=0,
            duration=0,
            distance=0,
        )
        db.add(new_set)
        
        await db.commit()
        await db.refresh(new_workout)
        
        # Return the created workout
        return WorkoutResponseSchema(
            id=new_workout.id,
            training_plan_id=new_workout.training_plan_id,
            name=new_workout.name,
            date_created=new_workout.date_created,
            description=new_workout.description,
            status=WorkoutStatusEnum.DONE,  # It's done since the single set is marked as done
        )
        
    except Exception as e:
        await db.rollback()
        print(f"Error creating manual activity workout: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to create workout from manual activity"
        )


def make_naive(dt: datetime) -> datetime:
    if dt is not None and dt.tzinfo is not None:
        return dt.replace(tzinfo=None)
    return dt


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


@router.post("/{workout_id}/revise/accept", response_model=WorkoutSchemaWithBlocks)
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
            
            # Calculate status for the updated workout
            calculated_status = calculate_workout_status(updated_workout)
            
            # Build response data
            response_blocks_data = []
            for block_orm in updated_workout.blocks:
                response_exercises_data = []
                for exercise_orm in block_orm.exercises:
                    response_sets_data = [SetResponseSchema.from_orm(s) for s in exercise_orm.sets]
                    response_exercises_data.append(
                        ExerciseResponseSchema(
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
                    BlockResponseSchema(
                        id=block_orm.id,
                        name=block_orm.name,
                        description=block_orm.description,
                        notes=block_orm.notes,
                        workout_id=block_orm.workout_id,
                        exercises=response_exercises_data
                    )
                )
            
            result = WorkoutSchemaWithBlocks(
                id=updated_workout.id,
                training_plan_id=updated_workout.training_plan_id,
                name=updated_workout.name,
                date_created=updated_workout.date_created,
                description=updated_workout.description,
                duration=updated_workout.duration,
                focus=updated_workout.focus,
                notes=updated_workout.notes,
                status=calculated_status,
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
