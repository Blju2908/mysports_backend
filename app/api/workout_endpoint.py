from fastapi import APIRouter, Depends, HTTPException, status, Body, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, join, update
from typing import List, Optional
from sqlalchemy.orm import selectinload
from datetime import datetime
from pydantic import BaseModel
from uuid import UUID

from app.models.workout_model import Workout
from app.schemas.workout_schema import (
    WorkoutResponseSchema,
    WorkoutSchemaWithBlocks,
    BlockResponseSchema,
    ActivityBlockPayloadSchema,
    ActivitySetSchema,
)
from app.schemas.workout_feedback_schema import WorkoutFeedbackSchema, WorkoutFeedbackResponseSchema
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.user_model import UserModel
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from app.models.training_history import ActivityLog
from app.models.workout_feedback_model import WorkoutFeedback
from app.models.user_model import UserModel
from app.services.workout_service import get_workout_details

router = APIRouter(tags=["workouts"])


@router.get("/", response_model=List[WorkoutResponseSchema])
async def get_user_workouts(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
    status: Optional[str] = None,
):
    """
    Get all workouts for the current user.
    Optionally filter by status (COMPLETED, INCOMPLETE, etc.)
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
        .order_by(Workout.date_created.desc())  # Hier date_created statt date verwenden
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
    "/{workout_id}/blocks/{block_id}/save-activity", status_code=status.HTTP_201_CREATED
)
async def save_activity_block_endpoint(
    workout_id: int,
    block_id: int,
    payload: ActivityBlockPayloadSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Saves the completed sets of a block as activity logs in the training history.
    Updates the block status to 'completed'.
    """
    # 1. Verify user access to the workout and get the block
    user_query = select(UserModel).where(UserModel.id == UUID(current_user.id))
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()

    if not user or not user.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User has no training plan",
        )

    # Fetch the specific block and verify it belongs to the workout and user
    block_query = (
        select(Block)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Block.id == block_id,
            Block.workout_id == workout_id,
            Workout.training_plan_id == user.training_plan_id,
        )
    )
    result = await db.execute(block_query)
    block_to_update = result.scalar_one_or_none()

    if not block_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Block not found or user does not have access",
        )

    # 2. Create ActivityLog entries for each set in the payload
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
            notes=activity_set.notes,
        )
        db.add(log_entry)

    db.add(block_to_update)

    # 4. Commit the transaction
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error saving activity block: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save activity log.",
        )

    return None


@router.delete("/{workout_id}", status_code=204)
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
    workout_query = select(Workout).where(
        Workout.id == workout_id, Workout.training_plan_id == UserModel.training_plan_id
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
        return {"success": True}
    except Exception as e:
        await db.rollback()
        print(f"Error deleting workout: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Fehler beim Löschen des Workouts."
        )


@router.post("/blocks/finish", status_code=status.HTTP_201_CREATED)
async def finish_block(
    payload: ActivityBlockPayloadSchema = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Setzt den Status eines Blocks auf 'done' und speichert die Sätze als ActivityLog.
    Erwartet: { block_id: int, workout_id: int, sets: [ { id, exercise_name, ..., notes? } ] }
    """
    # Block laden und prüfen
    block_query = select(Block).where(Block.id == payload.block_id)
    b_result = await db.execute(block_query)
    block_to_update = b_result.scalar_one_or_none()
    if not block_to_update:
        raise HTTPException(status_code=404, detail="Block nicht gefunden")
    
    # Optional: Prüfen, ob das Workout existiert und zum Block passt
    if payload.workout_id:
        workout_query = select(Workout).where(Workout.id == payload.workout_id)
        w_result = await db.execute(workout_query)
        workout = w_result.scalar_one_or_none()
        if not workout:
            raise HTTPException(status_code=404, detail="Workout nicht gefunden")
        if block_to_update.workout_id != payload.workout_id:
            raise HTTPException(status_code=400, detail="Block gehört nicht zum angegebenen Workout")

    # Block-Status setzen
    block_to_update.status = BlockStatus.done
    db.add(block_to_update)

    # ActivityLogs anlegen
    current_timestamp = datetime.utcnow()
    for activity_set in payload.sets:
        log_entry = ActivityLog(
            user_id=current_user.id,
            workout_id=payload.workout_id,  # Neu: Speichere die workout_id
            timestamp=current_timestamp,
            exercise_name=activity_set.exercise_name,
            set_id=activity_set.id,
            weight=activity_set.weight,
            reps=activity_set.reps,
            duration=activity_set.duration,
            distance=activity_set.distance,
            speed=activity_set.speed,
            rest_time=activity_set.rest_time,
            notes=activity_set.notes
        )
        db.add(log_entry)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error finishing block: {e}")
        raise HTTPException(
            status_code=500, detail="Fehler beim Abschließen des Blocks."
        )
    return {"success": True}


class ResetBlocksPayload(BaseModel):
    block_ids: list[int]

@router.put("/reset-blocks")
async def reset_blocks(
    payload: ResetBlocksPayload,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if not payload.block_ids or not isinstance(payload.block_ids, list):
        raise HTTPException(status_code=400, detail="block_ids müssen angegeben werden.")

    # prüfe, ob die Blöcke existieren
    block_query = select(Block).where(Block.id.in_(payload.block_ids))
    try:
        b_result = await db.execute(block_query)
        blocks = b_result.scalars().all()
    except Exception as e:
        print(f"DB-Fehler beim Laden der Blöcke: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Laden der Blöcke.")

    if not blocks:
        raise HTTPException(status_code=404, detail="Keine Blöcke gefunden.")

    # prüfe, ob alle angeforderten Blöcke gefunden wurden
    found_block_ids = {block.id for block in blocks}
    missing_ids = set(payload.block_ids) - found_block_ids
    if missing_ids:
        raise HTTPException(
            status_code=404,
            detail=f"Folgende Block-IDs wurden nicht gefunden: {sorted(missing_ids)}"
        )

    # setze den Status der Blöcke auf 'open'
    for block in blocks:
        block.status = BlockStatus.open
        db.add(block)

    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Fehler beim Zurücksetzen der Blöcke: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Zurücksetzen der Blöcke.")

    return {"success": True}


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
