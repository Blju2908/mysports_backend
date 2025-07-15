from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.llm_call_log_model import LlmOperationStatus
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.workout_model import Workout
from app.models.llm_call_log_model import LlmCallLog
from app.llm.workout_revision.workout_revision_schemas import (
    WorkoutRevisionRequestSchema,
)
# from app.llm.workout_revision.workout_revision_service import run_workout_revision_chain
from uuid import UUID
import logging
from sqlalchemy.orm import selectinload
from app.llm.workout_generation.workout_parser import update_existing_workout_with_compact_data, update_existing_workout_with_revision_data


router = APIRouter()
logger = logging.getLogger("llm_endpoint")


# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(None, description="Optional user prompt for workout generation")
    use_exercise_filtering: bool = Field(False, description="Enable exercise filtering based on user equipment and experience")


@router.post("/llm/start-workout-creation")
async def start_workout_creation(
    request_data: CreateWorkoutRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Startet die asynchrone Workout-Erstellung und gibt sofort eine workout_id zurück.
    ✅ NEU: Erstellt sofort einen Log-Eintrag mit Status STARTED für durchgängiges Tracking.
    """
    logger.info("[llm/start-workout] Start - User: %s, Exercise Filtering: %s", 
                current_user.id, request_data.use_exercise_filtering)
    
    try:
        # 1. Erstelle Placeholder-Workout in der DB
        placeholder_workout = Workout(
            user_id=UUID(current_user.id),
            name="Wird generiert...",
            description="Workout wird erstellt. Bitte warten..."
        )
        db.add(placeholder_workout)
        
        # Flush, um die workout_id vor dem Commit zu erhalten
        await db.flush()
        
        workout_id = placeholder_workout.id
        logger.info("[llm/start-workout] Placeholder-Workout erstellt mit ID: %s", workout_id)
        
        # ✅ Korrektur: Log-Eintrag erstellen, aber Commit aufschieben
        log_entry = LlmCallLog(
            user_id=current_user.id,
            endpoint_name="llm/start-workout-creation",
            llm_operation_type="workout_creation",
            status=LlmOperationStatus.STARTED,
            workout_id=workout_id
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
            log_id=log_id  # ✅ NEU: Log-ID für Status-Updates
        )
        
        return {
            "success": True,
            "message": "Workout-Erstellung gestartet",
            "data": {
                "workout_id": workout_id,
                "log_id": log_id  # Optional: Für Debugging
            }
        }
        
    except Exception as e:
        logger.error("[llm/start-workout] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Starten der Workout-Erstellung: {str(e)}"
        )


@router.get("/llm/workout-status/{workout_id}")
async def get_workout_status(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Prüft den Status einer asynchronen Workout-Erstellung.
    ✅ NEU: Wirft Exception wenn kein Log-Eintrag existiert (durchgängiges Tracking).
    """
    logger.info("[llm/workout-status] Checking status for workout_id: %s", workout_id)
    
    try:
        # ✅ NEU: Prüfe ZUERST ob Log-Eintrag existiert (Pflicht für durchgängiges Tracking)
        log_stmt = select(LlmCallLog).where(
            LlmCallLog.workout_id == workout_id,
            LlmCallLog.user_id == current_user.id
        ).order_by(LlmCallLog.timestamp.desc())
        
        log_result = await db.execute(log_stmt)
        llm_log = log_result.scalar_one_or_none()
        
        # ✅ NEU: Exception wenn kein Log existiert
        if not llm_log:
            logger.error("[llm/workout-status] Kein Log-Eintrag für workout_id: %s", workout_id)
            raise HTTPException(
                status_code=404,
                detail=f"Keine Workout-Erstellung für ID {workout_id} gefunden. Möglicherweise wurde das Workout nicht über start-workout-creation erstellt."
            )
        
        # 2. Status basierend auf Log-Eintrag bestimmen
        if llm_log.status == LlmOperationStatus.STARTED:
            return {
                "status": "generating",
                "message": "Workout wird generiert...",
                "workout_id": workout_id
            }
        elif llm_log.status == LlmOperationStatus.SUCCESS:
            return {
                "status": "completed",
                "message": "Workout erfolgreich erstellt",
                "workout_id": workout_id
            }
        elif llm_log.status == LlmOperationStatus.FAILED:
            return {
                "status": "failed",
                "message": f"Fehler bei der Erstellung: {llm_log.error_message or 'Unbekannter Fehler'}",
                "workout_id": workout_id
            }
        else:
            # Fallback für unbekannte Status
            logger.warning("[llm/workout-status] Unbekannter Status: %s für workout_id: %s", llm_log.status, workout_id)
            return {
                "status": "unknown",
                "message": f"Unbekannter Status: {llm_log.status}",
                "workout_id": workout_id
            }
            
    except HTTPException:
        # HTTPExceptions weiterleiten (z.B. 404 für fehlenden Log)
        raise
    except Exception as e:
        logger.error("[llm/workout-status] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Prüfen des Status: {str(e)}"
        )


# ✅ V2: Workout Revision Endpoints - Single Step Approach
@router.post("/llm/start-workout-revision")
async def start_workout_revision(
    request_data: WorkoutRevisionRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    V2: Startet die asynchrone Workout-Revision mit direkter Ersetzung.
    Keine JSON-Storage mehr - direkter atomischer Austausch.
    """
    workout_id = request_data.workout_id
    logger.info("[llm/start-workout-revision-v2] Start - User: %s, Workout: %s", 
                current_user.id, workout_id)
    
    try:
        # 1. Prüfe ob Workout existiert und User berechtigt ist
        workout_orm = await db.scalar(
            select(Workout)
            .where(
                Workout.id == workout_id,
                Workout.user_id == UUID(current_user.id)
            )
        )
        
        if not workout_orm:
            raise HTTPException(
                status_code=403,
                detail="Keine Berechtigung für den Zugriff auf dieses Workout"
            )
        
        # 2. Erstelle sofort Log-Eintrag mit Status STARTED
        log_entry = LlmCallLog(
            user_id=current_user.id,
            endpoint_name="llm/start-workout-revision-v2",
            llm_operation_type="workout_revision",
            status=LlmOperationStatus.STARTED,
            workout_id=workout_id
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(log_entry)
        
        log_id = log_entry.id
        logger.info("[llm/start-workout-revision-v2] Log-Eintrag erstellt mit ID: %s", log_id)
        
        # 3. Starte Background-Task für V2 Revision (direkter Austausch)
        from app.llm.workout_revision.workout_revision_service import revise_workout_background_v2
        
        background_tasks.add_task(
            revise_workout_background_v2,
            workout_id=workout_id,
            user_id=current_user.id,
            user_feedback=request_data.user_feedback,
            log_id=log_id
        )
        
        return {
            "success": True,
            "message": "Workout-Revision V2 gestartet",
            "data": {
                "workout_id": workout_id,
                "log_id": log_id
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[llm/start-workout-revision-v2] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Workout-Revision V2: {str(e)}"
        )


@router.get("/llm/workout-revision-status/{log_id}")
async def get_workout_revision_status(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    V2: Prüft den Status einer asynchronen Workout-Revision anhand der Log-ID.
    Vereinfacht da keine JSON-Storage mehr verwendet wird.
    """
    logger.info("[llm/workout-revision-status-v2] Checking status for log_id: %s", log_id)
    
    try:
        # Direkte Abfrage nach log_id
        log_stmt = select(LlmCallLog).where(
            LlmCallLog.id == log_id,
            LlmCallLog.user_id == current_user.id,
            LlmCallLog.llm_operation_type == "workout_revision"
        )
        
        log_result = await db.execute(log_stmt)
        llm_log = log_result.scalar_one_or_none()
        
        if not llm_log:
            logger.error("[llm/workout-revision-status-v2] Kein Log-Eintrag für log_id: %s", log_id)
            raise HTTPException(
                status_code=404,
                detail=f"Keine Workout-Revision für Log-ID {log_id} gefunden."
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
            # ✅ NEU: Lade das Workout und gib die Revisionsdaten zurück
            workout_stmt = select(Workout).where(Workout.id == workout_id)
            workout_result = await db.execute(workout_stmt)
            workout = workout_result.scalar_one_or_none()

            if not workout:
                 logger.error(f"[llm/workout-revision-status-v2] Workout {workout_id} nicht gefunden für Log {log_id}")
                 raise HTTPException(status_code=404, detail=f"Zugehöriges Workout {workout_id} nicht gefunden.")

            has_data = workout.revised_workout_data is not None
            return {
                "status": "completed",
                "message": "Workout-Revision erfolgreich abgeschlossen",
                "workout_id": workout_id,
                "log_id": log_id,
                "has_revision_data": has_data,
                "revision_data": workout.revised_workout_data
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
            logger.warning("[llm/workout-revision-status-v2] Unbekannter Status: %s für log_id: %s", llm_log.status, log_id)
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
        logger.error("[llm/workout-revision-status-v2] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Prüfen des Revision-Status: {str(e)}"
        )


@router.post("/llm/accept-workout-revision")
async def accept_workout_revision(
    workout_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Applies the pending revision to the workout.
    """
    logger.info(f"[accept_workout_revision] Accepting revision for workout_id: {workout_id}")
    
    try:
        # Load workout with blocks eagerly
        stmt = select(Workout).options(
            selectinload(Workout.blocks).selectinload('*')
        ).where(
            Workout.id == workout_id,
            Workout.user_id == UUID(current_user.id)
        )
        result = await db.execute(stmt)
        workout = result.scalar_one_or_none()
        
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found or access denied")
        
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
            "workout_id": workout_id
        }
    except Exception as e:
        await db.rollback()
        logger.error(f"[accept_workout_revision] Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error applying revision: {str(e)}")


async def generate_workout_background(
    workout_id: int,
    user_id: str,
    request_data: CreateWorkoutRequest,
    log_id: int,
):
    """
    ✅ REFACTORED: Background task for V2 workout generation.
    Follows the clean architecture from test_workout_generation_v2.py:
    1. Gathers all necessary data strings.
    2. Calls the pure LLM chain function.
    3. Parses the result into DB models.
    4. Updates the placeholder workout in the database.
    """
    logger.info(f"[generate_workout_background_v2] Starting for workout_id: {workout_id}")

    from app.services.llm_logging_service import log_operation_success, log_operation_failed, OperationTimer
    from app.models.training_plan_model import TrainingPlan
    from sqlalchemy import select
    from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm
    from app.llm.workout_generation.workout_utils import summarize_training_history
    from app.db.workout_db_access import get_training_history_for_user_from_db
    from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
    from app.llm.workout_generation.workout_generation_chain_v2 import execute_workout_generation_sequence_v2
    from app.llm.workout_generation.workout_parser import parse_compact_workout_to_db_models
    from app.db.session import get_background_session
    from sqlalchemy.orm import selectinload

    timer = OperationTimer()
    timer.start()

    user_id_uuid = UUID(user_id)

    try:
        # --- STEP 1: Gather all necessary data in one DB session ---
        formatted_training_plan = None
        summarized_history_str = None
        exercise_library_str = ""
        training_plan_id_for_saving = None

        async with get_background_session() as db:
            logger.info("[generate_workout_background_v2] Loading user data from DB...")

            # Load and format TrainingPlan
            training_plan_db_obj = await db.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
            )
            if training_plan_db_obj:
                training_plan_id_for_saving = training_plan_db_obj.id
                formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
                logger.info("[generate_workout_background_v2] Training plan loaded and formatted.")

            # Load, summarize, and format Training History
            raw_training_history = await get_training_history_for_user_from_db(
                user_id_uuid, db, limit=10
            )
            if raw_training_history:
                summarized_history_str = summarize_training_history(raw_training_history)
                logger.info("[generate_workout_background_v2] Training history loaded and summarized.")

            # Load exercise library
            exercise_library_str = await get_all_exercises_for_prompt(db)
            logger.info(f"[generate_workout_background_v2] Loaded {len(exercise_library_str.splitlines())} exercises.")

        logger.info("[generate_workout_background_v2] DB data gathering complete. Starting LLM generation...")

        # --- STEP 2: Execute LLM chain (no DB connection) ---
        compact_workout_schema = await execute_workout_generation_sequence_v2(
            training_plan_str=formatted_training_plan,
            training_history_str=summarized_history_str,
            user_prompt=request_data.prompt,
            exercise_library_str=exercise_library_str,
        )

        logger.info("[generate_workout_background_v2] LLM generation completed. Saving to DB...")

        # --- STEP 3: Parse and save results to the DB ---
        async with get_background_session() as save_db:
            # Load the placeholder workout eagerly
            stmt = select(Workout).options(
                selectinload(Workout.blocks).selectinload('*')
            ).where(Workout.id == workout_id)
            result = await save_db.execute(stmt)
            placeholder_workout = result.scalar_one_or_none()

            if not placeholder_workout:
                raise ValueError(f"Placeholder workout with ID {workout_id} not found.")

            # ✅ FIX: Delete existing blocks first to avoid orphaned records
            for block in placeholder_workout.blocks:
                await save_db.delete(block)
            await save_db.flush()

            # ✅ FIX: Update existing workout directly instead of creating new one
            update_existing_workout_with_compact_data(
                existing_workout=placeholder_workout,
                compact_workout=compact_workout_schema,
                training_plan_id=training_plan_id_for_saving,
            )
            
            save_db.add(placeholder_workout)
            await save_db.commit()
            
            logger.info(f"[generate_workout_background_v2] Workout {workout_id} successfully updated.")

        # --- STEP 4: Log success ---
        async with get_background_session() as log_db:
            await log_operation_success(
                db=log_db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )

        logger.info(f"[generate_workout_background_v2] Completed successfully in {timer.get_duration_ms()}ms")

    except Exception as e:
        logger.error(f"[generate_workout_background_v2] Error: {e}", exc_info=True)
        # Log failure in a separate session
        try:
            async with get_background_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms()
                )
        except Exception as log_e:
            logger.error(f"[generate_workout_background_v2] CRITICAL: Failed to log error: {log_e}")