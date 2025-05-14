from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join, update
from typing import List, Optional
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
from app.schemas.workout_schema import (
    WorkoutResponseSchema,
    WorkoutSchemaWithBlocks,
    BlockResponseSchema,
    SetResponseSchema,
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


@router.get("/", response_model=List[WorkoutResponseSchema])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get all workouts for the current user.
    """
    # Hole den User mit seinem Trainingsplan
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        return []  # User hat keinen Trainingsplan

    # Hole die Workouts des Trainingsplans
    workout_query = (
        select(Workout)
        .where(Workout.training_plan_id == user.training_plan_id)
        .order_by(Workout.date_created.desc())
    )

    result = await db.execute(workout_query)
    workouts = result.scalars().all()

    return workouts


@router.get("/{workout_id}", response_model=WorkoutSchemaWithBlocks)
async def get_workout_detail(
    workout_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Get detailed information about a specific workout including all blocks and exercises.
    Uses the workout service for logic and authorization.
    """
    # Call the service function, exceptions will propagate
    workout = await get_workout_details(workout_id=workout_id, db=db)
    
    # Überprüfe, ob der User Zugriff auf dieses Workout hat
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if (not user or not user.training_plan_id or 
        workout.training_plan_id != user.training_plan_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Keine Berechtigung für den Zugriff auf dieses Workout"
        )
    
    return workout


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

    return block


@router.post(
    "/{workout_id}/blocks/{block_id}/save-activity", status_code=status.HTTP_200_OK
)
async def save_block_activity_endpoint( 
    workout_id: int, # Path parameter
    block_id: int,   # Path parameter
    payload: BlockActivityPayload, # Uses updated BlockActivityPayload
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Saves the execution data for specified sets within a block.
    Payload includes block_id, workout_id, and a list of sets (each with set_id, status, and execution data).
    """
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    user_result = await db.execute(user_query)
    user = user_result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no training plan.",
        )
    
    # Validate path params match payload params before hitting DB for the block
    if payload.block_id != block_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payload block_id {payload.block_id} does not match path block_id {block_id}."
        )
    if payload.workout_id != workout_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Payload workout_id {payload.workout_id} does not match path workout_id {workout_id}."
        )

    block_query = (
        select(Block)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == payload.block_id, # Use payload.block_id which is validated against path param
            Workout.id == payload.workout_id, # Use payload.workout_id for the join condition
            Workout.training_plan_id == user.training_plan_id,
        )
    )
    block_result = await db.execute(block_query)
    db_block = block_result.scalar_one_or_none()

    if not db_block:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Block with id {payload.block_id} in workout {payload.workout_id} not found or user does not have access.",
        )

    updated_set_ids = []
    for set_data in payload.sets: # set_data is now SetExecutionInputSchema, which has set_id
        set_query = select(Set).where(Set.id == set_data.set_id, Set.exercise.has(Exercise.block_id == db_block.id))
        set_result = await db.execute(set_query)
        db_set = set_result.scalar_one_or_none()

        if not db_set:
            print(f"Set with id {set_data.set_id} not found in block {db_block.id}. Skipping.")
            continue

        if set_data.weight is not None:
            db_set.weight = set_data.weight
        if set_data.reps is not None:
            db_set.reps = set_data.reps
        if set_data.duration is not None:
            db_set.duration = set_data.duration
        if set_data.distance is not None:
            db_set.distance = set_data.distance
        if set_data.notes is not None: 
            db_set.notes = set_data.notes

        db_set.status = set_data.status
        if set_data.status == SetStatus.done:
            db_set.completed_at = set_data.completed_at if set_data.completed_at else datetime.utcnow()
        else:
            db_set.completed_at = None 

        db.add(db_set)
        updated_set_ids.append(db_set.id)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error saving block activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save block activity.",
        )

    return {"message": f"Activity for block {db_block.id} saved. Updated sets: {updated_set_ids}"}


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
