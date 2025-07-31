# Fixed imports
from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
import logging

from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.db.session import create_session
from app.services.llm_logging_service import (
    log_operation_success,
    log_operation_failed,
    OperationTimer,
)
from app.models.llm_call_log_model import LlmOperationStatus
from app.models.workout_model import Workout
from app.models.llm_call_log_model import LlmCallLog

from app.llm.workout_revision.workout_revision_schemas import (
    WorkoutRevisionRequestSchema,
)

# Workout Generation Base Imports
from app.llm.workout_generation.workout_parser import (
    update_existing_workout_with_revision_data,
)

# Compressed Workout Generation Imports
from app.llm.workout_generation_v1.versions.compressed_20250731.service import (
    generate_compressed_workout,
    CompressedWorkoutInput,
    parse_compressed_workout_to_db_models,
)


router = APIRouter()
logger = logging.getLogger("llm_endpoint")


# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(
        None, description="Optional user prompt for workout generation"
    )
    profile_id: int | None = Field(
        None, description="Optional profile ID for workout generation"
    )
    duration_minutes: int | None = Field(
        None, description="Optional duration in minutes for workout generation"
    )


@router.post("/llm/start-workout-creation")
async def start_workout_creation(
    request_data: CreateWorkoutRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Startet die asynchrone Workout-Erstellung und gibt sofort eine workout_id zurück.
    ✅ NEU: Erstellt sofort einen Log-Eintrag mit Status STARTED für durchgängiges Tracking.
    """

    try:
        # 1. Erstelle Placeholder-Workout in der DB
        placeholder_workout = Workout(
            user_id=UUID(current_user.id),
            name="Wird generiert...",
            description="Workout wird erstellt. Bitte warten...",
        )
        db.add(placeholder_workout)

        # Flush, um die workout_id vor dem Commit zu erhalten
        await db.flush()

        workout_id = placeholder_workout.id
        logger.info(
            "[llm/start-workout] Placeholder-Workout erstellt mit ID: %s", workout_id
        )

        # ✅ Korrektur: Log-Eintrag erstellen, aber Commit aufschieben
        log_entry = LlmCallLog(
            user_id=current_user.id,
            endpoint_name="llm/start-workout-creation",
            llm_operation_type="workout_creation",
            status=LlmOperationStatus.STARTED,
            workout_id=workout_id,
        )
        db.add(log_entry)

        # Transaktion für beide Objekte committen
        await db.commit()

        # Jetzt die Objekte refreshen, um die DB-generierten Werte zu laden
        await db.refresh(placeholder_workout)
        await db.refresh(log_entry)

        log_id = log_entry.id
        logger.info("[llm/start-workout] Log-Eintrag erstellt mit ID: %s", log_id)

        # 2. Starte Background-Task mit log_id für Status-Updates
        background_tasks.add_task(
            generate_workout_background,
            workout_id=workout_id,
            user_id=current_user.id,
            request_data=request_data,
            session_duration=request_data.duration_minutes,
            profile_id=request_data.profile_id,
            log_id=log_id,
        )

        return {
            "success": True,
            "message": "Workout-Erstellung gestartet",
            "data": {
                "workout_id": workout_id,
                "log_id": log_id,  # Optional: Für Debugging
            },
        }

    except Exception as e:
        logger.error("[llm/start-workout] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Workout-Erstellung: {str(e)}",
        )


@router.get("/llm/workout-status/{workout_id}")
async def get_workout_status(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Prüft den Status einer asynchronen Workout-Erstellung.
    ✅ NEU: Wirft Exception wenn kein Log-Eintrag existiert (durchgängiges Tracking).
    """
    logger.info("[llm/workout-status] Checking status for workout_id: %s", workout_id)

    try:
        # ✅ NEU: Prüfe ZUERST ob Log-Eintrag existiert (Pflicht für durchgängiges Tracking)
        log_stmt = (
            select(LlmCallLog)
            .where(
                LlmCallLog.workout_id == workout_id,
                LlmCallLog.user_id == current_user.id,
            )
            .order_by(LlmCallLog.timestamp.desc())
        )

        log_result = await db.execute(log_stmt)
        llm_log = log_result.scalar_one_or_none()

        # ✅ NEU: Exception wenn kein Log existiert
        if not llm_log:
            logger.error(
                "[llm/workout-status] Kein Log-Eintrag für workout_id: %s", workout_id
            )
            raise HTTPException(
                status_code=404,
                detail=f"Keine Workout-Erstellung für ID {workout_id} gefunden. Möglicherweise wurde das Workout nicht über start-workout-creation erstellt.",
            )

        # 2. Status basierend auf Log-Eintrag bestimmen
        if llm_log.status == LlmOperationStatus.STARTED:
            return {
                "status": "generating",
                "message": "Workout wird generiert...",
                "workout_id": workout_id,
            }
        elif llm_log.status == LlmOperationStatus.SUCCESS:
            return {
                "status": "completed",
                "message": "Workout erfolgreich erstellt",
                "workout_id": workout_id,
            }
        elif llm_log.status == LlmOperationStatus.FAILED:
            return {
                "status": "failed",
                "message": f"Fehler bei der Erstellung: {llm_log.error_message or 'Unbekannter Fehler'}",
                "workout_id": workout_id,
            }
        else:
            # Fallback für unbekannte Status
            logger.warning(
                "[llm/workout-status] Unbekannter Status: %s für workout_id: %s",
                llm_log.status,
                workout_id,
            )
            return {
                "status": "unknown",
                "message": f"Unbekannter Status: {llm_log.status}",
                "workout_id": workout_id,
            }

    except HTTPException:
        # HTTPExceptions weiterleiten (z.B. 404 für fehlenden Log)
        raise
    except Exception as e:
        logger.error("[llm/workout-status] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Fehler beim Prüfen des Status: {str(e)}"
        )


# ✅ V2: Workout Revision Endpoints - Single Step Approach
@router.post("/llm/start-workout-revision")
async def start_workout_revision(
    request_data: WorkoutRevisionRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    V2: Startet die asynchrone Workout-Revision mit direkter Ersetzung.
    Keine JSON-Storage mehr - direkter atomischer Austausch.
    """
    workout_id = request_data.workout_id
    logger.info(
        "[llm/start-workout-revision-v2] Start - User: %s, Workout: %s",
        current_user.id,
        workout_id,
    )

    try:
        # 1. Prüfe ob Workout existiert und User berechtigt ist
        workout_orm = await db.scalar(
            select(Workout).where(
                Workout.id == workout_id, Workout.user_id == UUID(current_user.id)
            )
        )

        if not workout_orm:
            raise HTTPException(
                status_code=403,
                detail="Keine Berechtigung für den Zugriff auf dieses Workout",
            )

        # 2. Erstelle sofort Log-Eintrag mit Status STARTED
        log_entry = LlmCallLog(
            user_id=current_user.id,
            endpoint_name="llm/start-workout-revision-v2",
            llm_operation_type="workout_revision",
            status=LlmOperationStatus.STARTED,
            workout_id=workout_id,
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)

        log_id = log_entry.id
        logger.info(
            "[llm/start-workout-revision-v2] Log-Eintrag erstellt mit ID: %s", log_id
        )

        # 3. Starte Background-Task für V2 Revision (direkter Austausch)
        from app.llm.workout_revision.workout_revision_service import (
            revise_workout_background_v2,
        )

        background_tasks.add_task(
            revise_workout_background_v2,
            workout_id=workout_id,
            user_id=current_user.id,
            user_feedback=request_data.user_feedback,
            log_id=log_id,
        )

        return {
            "success": True,
            "message": "Workout-Revision V2 gestartet",
            "data": {"workout_id": workout_id, "log_id": log_id},
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "[llm/start-workout-revision-v2] Exception: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Workout-Revision V2: {str(e)}",
        )


@router.get("/llm/workout-revision-status/{log_id}")
async def get_workout_revision_status(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    V2: Prüft den Status einer asynchronen Workout-Revision anhand der Log-ID.
    Vereinfacht da keine JSON-Storage mehr verwendet wird.
    """
    logger.info(
        "[llm/workout-revision-status-v2] Checking status for log_id: %s", log_id
    )

    try:
        # Direkte Abfrage nach log_id
        log_stmt = select(LlmCallLog).where(
            LlmCallLog.id == log_id,
            LlmCallLog.user_id == current_user.id,
            LlmCallLog.llm_operation_type == "workout_revision",
        )

        log_result = await db.execute(log_stmt)
        llm_log = log_result.scalar_one_or_none()

        if not llm_log:
            logger.error(
                "[llm/workout-revision-status-v2] Kein Log-Eintrag für log_id: %s",
                log_id,
            )
            raise HTTPException(
                status_code=404,
                detail=f"Keine Workout-Revision für Log-ID {log_id} gefunden.",
            )

        workout_id = llm_log.workout_id

        # Status basierend auf Log-Eintrag bestimmen
        if llm_log.status == LlmOperationStatus.STARTED:
            return {
                "status": "revising",
                "message": "Workout wird überarbeitet...",
                "workout_id": workout_id,
                "log_id": log_id,
                "has_revision_data": False,
                "revision_data": None,
            }
        elif llm_log.status == LlmOperationStatus.SUCCESS:
            workout_stmt = select(Workout).where(Workout.id == workout_id)
            workout_result = await db.execute(workout_stmt)
            workout = workout_result.scalar_one_or_none()

            if not workout:
                logger.error(
                    f"[llm/workout-revision-status-v2] Workout {workout_id} nicht gefunden für Log {log_id}"
                )
                raise HTTPException(
                    status_code=404,
                    detail=f"Zugehöriges Workout {workout_id} nicht gefunden.",
                )

            has_data = workout.revised_workout_data is not None
            return {
                "status": "completed",
                "message": "Workout-Revision erfolgreich abgeschlossen",
                "workout_id": workout_id,
                "log_id": log_id,
                "has_revision_data": has_data,
                "revision_data": workout.revised_workout_data,
            }
        elif llm_log.status == LlmOperationStatus.FAILED:
            return {
                "status": "failed",
                "message": f"Fehler bei der Revision: {llm_log.error_message or 'Unbekannter Fehler'}",
                "workout_id": workout_id,
                "log_id": log_id,
                "has_revision_data": False,
                "revision_data": None,
            }
        else:
            logger.warning(
                "[llm/workout-revision-status-v2] Unbekannter Status: %s für log_id: %s",
                llm_log.status,
                log_id,
            )
            return {
                "status": "unknown",
                "message": f"Unbekannter Status: {llm_log.status}",
                "workout_id": workout_id,
                "log_id": log_id,
                "has_revision_data": False,
                "revision_data": None,
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "[llm/workout-revision-status-v2] Exception: %s", str(e), exc_info=True
        )
        raise HTTPException(
            status_code=500, detail=f"Fehler beim Prüfen des Revision-Status: {str(e)}"
        )


async def update_workout_in_database(
    db: AsyncSession,
    workout_id: int,
    new_workout_data: Workout,
    preserve_user_data: bool = True
) -> Workout:
    """
    Generic function to update a workout in the database.
    
    Args:
        db: Database session
        workout_id: ID of the workout to update
        new_workout_data: New workout data (DB model)
        preserve_user_data: Whether to preserve user_id and other user-specific fields
        
    Returns:
        Updated workout object
    """
    # Load existing workout with all relationships
    stmt = (
        select(Workout)
        .options(selectinload(Workout.blocks).selectinload("*"))
        .where(Workout.id == workout_id)
    )
    result = await db.execute(stmt)
    existing_workout = result.scalar_one_or_none()
    
    if not existing_workout:
        raise ValueError(f"Workout with ID {workout_id} not found")
    
    # Preserve important fields
    preserved_user_id = existing_workout.user_id if preserve_user_data else new_workout_data.user_id
    
    # Delete existing blocks
    for block in existing_workout.blocks:
        await db.delete(block)
    await db.flush()
    
    # Update workout fields
    existing_workout.name = new_workout_data.name
    existing_workout.description = new_workout_data.description
    existing_workout.duration = new_workout_data.duration
    existing_workout.focus = new_workout_data.focus
    existing_workout.muscle_group_load = new_workout_data.muscle_group_load
    existing_workout.focus_derivation = new_workout_data.focus_derivation
    existing_workout.notes = new_workout_data.notes
    existing_workout.training_plan_id = new_workout_data.training_plan_id
    
    # Preserve user_id
    existing_workout.user_id = preserved_user_id
    
    # Add new blocks from new_workout_data
    existing_workout.blocks = new_workout_data.blocks
    
    db.add(existing_workout)
    await db.commit()
    await db.refresh(existing_workout)
    
    return existing_workout


@router.post("/llm/accept-workout-revision")
async def accept_workout_revision(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Applies the pending revision to the workout.
    """
    logger.info(
        f"[accept_workout_revision] Accepting revision for workout_id: {workout_id}"
    )

    try:
        # Load workout with blocks eagerly
        stmt = (
            select(Workout)
            .options(selectinload(Workout.blocks).selectinload("*"))
            .where(Workout.id == workout_id, Workout.user_id == UUID(current_user.id))
        )
        result = await db.execute(stmt)
        workout = result.scalar_one_or_none()

        if not workout:
            raise HTTPException(
                status_code=404, detail="Workout not found or access denied"
            )

        if not workout.revised_workout_data:
            raise HTTPException(status_code=400, detail="No pending revision found")

        # ✅ FIX: Clear blocks before updating to avoid session conflicts
        # Store the blocks to delete them explicitly
        blocks_to_delete = list(workout.blocks)
        for block in blocks_to_delete:
            await db.delete(block)
        await db.flush()

        # ✅ CRITICAL FIX: Clear the blocks list to remove references to deleted objects
        workout.blocks = []

        # Refresh the workout to ensure it's clean after block deletion
        await db.refresh(workout)

        # ✅ FIX: Update existing workout directly from revision data
        update_existing_workout_with_revision_data(
            existing_workout=workout,
            revision_data=workout.revised_workout_data,
        )

        # Clear revision data
        workout.revised_workout_data = None

        db.add(workout)

        await db.commit()
        await db.refresh(workout)

        return {
            "success": True,
            "message": "Revision applied successfully",
            "workout_id": workout_id,
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"[accept_workout_revision] Error: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error applying revision: {str(e)}"
        )


async def generate_workout_background(
    workout_id: int,
    user_id: str,
    request_data: CreateWorkoutRequest,
    log_id: int,
    session_duration: int | None = None,
    profile_id: int | None = None,
):
    """
    ✅ REFACTORED: Background task for compressed workout generation.
    Uses the compressed format with ~90% token reduction.
    Clean separation: Generation → Parsing → Database Update
    """
    logger.info(
        f"[generate_workout_background_v2] Starting compressed generation for workout_id: {workout_id}"
    )

    timer = OperationTimer()
    timer.start()

    user_id_uuid = UUID(user_id)

    try:
        # --- STEP 1: Generate compressed workout ---
        input_data = CompressedWorkoutInput(
            user_id=user_id_uuid,
            user_prompt=request_data.prompt or "",
            profile_id=profile_id
        )
        
        logger.info("[generate_workout_background_v2] Starting compressed workout generation...")
        
        # Generate workout using compressed format
        full_prompt, workout_output = await generate_compressed_workout(
            input_data=input_data
        )
        
        if not workout_output.workout:
            raise ValueError("Workout generation failed - no workout returned")
        
        logger.info(
            f"[generate_workout_background_v2] Compressed generation completed. "
            f"Token reduction: {workout_output.token_reduction}, "
            f"Exercise count: {workout_output.exercise_count}"
        )

        # --- STEP 2: Parse to database models ---
        logger.info("[generate_workout_background_v2] Parsing compressed workout to DB models...")
        
        # Determine training_plan_id
        training_plan_id = None
        if profile_id:
            # The compressed service handles training plan lookup internally
            # We need to extract it from the generation context
            # For now, we'll need to do a quick DB lookup
            async with create_session() as db:
                from app.models.training_plan_model import TrainingPlan
                training_plan = await db.scalar(
                    select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
                )
                if training_plan:
                    training_plan_id = training_plan.id
        
        # Parse compressed format to DB models
        workout_db_model = await parse_compressed_workout_to_db_models(
            workout_schema=workout_output.workout,
            user_id=user_id_uuid,
            training_plan_id=training_plan_id
        )

        # --- STEP 3: Update workout in database ---
        logger.info("[generate_workout_background_v2] Updating workout in database...")
        
        async with create_session() as save_db:
            await update_workout_in_database(
                db=save_db,
                workout_id=workout_id,
                new_workout_data=workout_db_model,
                preserve_user_data=True
            )

        logger.info(
            f"[generate_workout_background_v2] Workout {workout_id} successfully updated."
        )

        # --- STEP 4: Log success ---
        async with create_session() as log_db:
            await log_operation_success(
                db=log_db, log_id=log_id, duration_ms=timer.get_duration_ms()
            )

        logger.info(
            f"[generate_workout_background_v2] Completed successfully in {timer.get_duration_ms()}ms"
        )

    except Exception as e:
        logger.error(f"[generate_workout_background_v2] Error: {e}", exc_info=True)
        # Log failure in a separate session
        try:
            async with create_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms(),
                )
        except Exception as log_e:
            logger.error(
                f"[generate_workout_background_v2] CRITICAL: Failed to log error: {log_e}"
            )
