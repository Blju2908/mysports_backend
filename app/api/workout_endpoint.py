from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join, update, delete
from typing import List, Optional, Union
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
from app.llm.schemas.workout_schema import (
    WorkoutResponseSchema,
    WorkoutSchemaWithBlocks,
    BlockResponseSchema,
    ExerciseResponseSchema,
    SetResponseSchema,
    WorkoutStatusEnum,
    BlockSchema
)
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


@router.get("/", response_model=List[WorkoutResponseSchema])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get all workouts for the current user.
    """
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        return []

    workout_query = (
        select(Workout)
        .where(Workout.training_plan_id == user.training_plan_id)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .order_by(Workout.date_created.desc())
    )

    result = await db.execute(workout_query)
    workouts_orm = result.scalars().all()

    response_workouts = []
    for workout_orm_item in workouts_orm:
        status = calculate_workout_status(workout_orm_item)
        response_workout = WorkoutResponseSchema(
            id=workout_orm_item.id,
            training_plan_id=workout_orm_item.training_plan_id,
            name=workout_orm_item.name,
            date_created=workout_orm_item.date_created,
            description=workout_orm_item.description,
            duration=workout_orm_item.duration,
            focus=workout_orm_item.focus,
            notes=workout_orm_item.notes,
            status=status,
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
    Get detailed information about a specific workout including all blocks and exercises.
    Calculates and includes workout status.
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
    
    calculated_status = calculate_workout_status(workout_orm)

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


@router.get("/feedback/{workout_id}", response_model=WorkoutFeedbackResponseSchema)
async def get_workout_feedback(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Holt das Feedback eines Users zu einem bestimmten Workout
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
    
    if not feedback:
        raise HTTPException(status_code=404, detail="Kein Feedback für dieses Workout gefunden")
    
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
        db_set.completed_at = payload.completed_at if payload.completed_at else datetime.utcnow()
    else:
        db_set.completed_at = None # Clear if not 'done'

    if payload.execution_weight is not None:
        db_set.execution_weight = payload.execution_weight
    if payload.execution_reps is not None:
        db_set.execution_reps = payload.execution_reps
    if payload.execution_duration is not None:
        db_set.execution_duration = payload.execution_duration
    if payload.execution_distance is not None:
        db_set.execution_distance = payload.execution_distance
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
