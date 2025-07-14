from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.llm.workout_generation.create_workout_service import run_workout_chain
from app.services.llm_logging_service import (
    log_operation_start, 
    log_operation_success, 
    log_operation_failed,
    log_workout_revision_start,
    log_workout_revision_accept,
    OperationTimer
)
from app.models.llm_call_log_model import LlmOperationStatus
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.workout_model import Workout
from app.models.llm_call_log_model import LlmCallLog
from app.llm.workout_revision.workout_revision_schemas import (
    WorkoutRevisionRequestSchema,
    WorkoutRevisionResponseSchema
)
from app.llm.workout_revision.workout_revision_service import run_workout_revision_chain
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from uuid import UUID
import logging


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


# ✅ NEW: Workout Revision Endpoints
@router.post("/llm/start-workout-revision")
async def start_workout_revision(
    request_data: WorkoutRevisionRequestSchema,
    background_tasks: BackgroundTasks,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Startet die asynchrone Workout-Revision und gibt sofort eine Bestätigung zurück.
    ✅ IMPROVED: workout_id kommt jetzt aus dem Body, nicht aus der URL.
    """
    workout_id = request_data.workout_id
    logger.info("[llm/start-workout-revision] Start - User: %s, Workout: %s", 
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
        log_id = await log_workout_revision_start(
            db=db,
            user_id=current_user.id,
            workout_id=workout_id,
            request_data={
                "user_feedback": request_data.user_feedback,
                "has_training_plan": request_data.training_plan is not None,
                "has_training_history": request_data.training_history is not None and len(request_data.training_history) > 0
            }
        )
        
        logger.info("[llm/start-workout-revision] Log-Eintrag erstellt mit ID: %s", log_id)
        
        # 3. Starte Background-Task für Revision
        background_tasks.add_task(
            revise_workout_background,
            workout_id=workout_id,
            user_id=current_user.id,
            request_data=request_data,
            log_id=log_id
        )
        
        return {
            "success": True,
            "message": "Workout-Revision gestartet",
            "data": {
                "workout_id": workout_id,
                "log_id": log_id  # ✅ IMPORTANT: Frontend soll log_id für Status-Abfragen nutzen
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[llm/start-workout-revision] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Starten der Workout-Revision: {str(e)}"
        )


@router.get("/llm/workout-revision-status/{log_id}")
async def get_workout_revision_status(
    log_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    Prüft den Status einer asynchronen Workout-Revision anhand der Log-ID.
    ✅ IMPROVED: Nutzt log_id statt workout_id um Multiple Results zu vermeiden.
    """
    logger.info("[llm/workout-revision-status] Checking status for log_id: %s", log_id)
    
    try:
        # ✅ IMPROVED: Direkte Abfrage nach log_id (eindeutig!)
        log_stmt = select(LlmCallLog).where(
            LlmCallLog.id == log_id,
            LlmCallLog.user_id == current_user.id,
            LlmCallLog.llm_operation_type == "workout_revision"
        )
        
        log_result = await db.execute(log_stmt)
        llm_log = log_result.scalar_one_or_none()
        
        if not llm_log:
            logger.error("[llm/workout-revision-status] Kein Log-Eintrag für log_id: %s", log_id)
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
                "log_id": log_id
            }
        elif llm_log.status == LlmOperationStatus.SUCCESS:
            # ✅ NEW: Bei erfolgreichem Status auch Revision-Daten laden
            workout_stmt = select(Workout).where(
                Workout.id == workout_id,
                Workout.user_id == current_user.id
            )
            workout_result = await db.execute(workout_stmt)
            workout_obj = workout_result.scalar_one_or_none()
            
            if workout_obj and workout_obj.has_pending_revision():
                return {
                    "status": "completed",
                    "message": "Workout-Revision erfolgreich abgeschlossen",
                    "workout_id": workout_id,
                    "log_id": log_id,
                    "has_revision_data": True,
                    "revision_data": workout_obj.get_revision_data()
                }
            else:
                return {
                    "status": "completed",
                    "message": "Workout-Revision erfolgreich abgeschlossen",
                    "workout_id": workout_id,
                    "log_id": log_id,
                    "has_revision_data": False
                }
        elif llm_log.status == LlmOperationStatus.FAILED:
            return {
                "status": "failed",
                "message": f"Fehler bei der Revision: {llm_log.error_message or 'Unbekannter Fehler'}",
                "workout_id": workout_id,
                "log_id": log_id
            }
        else:
            logger.warning("[llm/workout-revision-status] Unbekannter Status: %s für log_id: %s", llm_log.status, log_id)
            return {
                "status": "unknown",
                "message": f"Unbekannter Status: {llm_log.status}",
                "workout_id": workout_id,
                "log_id": log_id
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[llm/workout-revision-status] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Prüfen des Revision-Status: {str(e)}"
        )


@router.post("/llm/accept-workout-revision")
async def accept_workout_revision_endpoint(
    workout_id: int,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    """
    ✅ REFACTORED: Akzeptiert eine Workout-Revision aus der JSON-Spalte.
    Nutzt den neuen Service für saubere Trennung der Logik.
    """
    logger.info("[llm/accept-workout-revision] Start - User: %s, Workout: %s", 
                current_user.id, workout_id)
    
    try:
        # ✅ NEW: Nutze den Service für Accept-Logik
        from app.llm.workout_revision.workout_revision_service import accept_workout_revision
        
        updated_workout = await accept_workout_revision(
            workout_id=workout_id,
            user_id=current_user.id,
            db=db
        )
        
        logger.info("[llm/accept-workout-revision] Workout-Revision erfolgreich übernommen: %s", workout_id)
        
        return {
            "success": True,
            "message": "Workout-Revision erfolgreich übernommen",
            "data": {
                "workout_id": workout_id
            }
        }
        
    except ValueError as ve:
        logger.error("[llm/accept-workout-revision] Validation error: %s", str(ve))
        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("[llm/accept-workout-revision] Exception: %s", str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Fehler beim Übernehmen der Workout-Revision: {str(e)}"
        )


async def generate_workout_background(
    workout_id: int,
    user_id: str,
    request_data: CreateWorkoutRequest,
    log_id: int
):
    """
    ✅ OPTIMIZED: Background task for workout generation - DB operations separated from LLM calls
    """
    logger.info(f"[generate_workout_background] Starting workout_id: {workout_id}")
    
    from app.services.llm_logging_service import log_operation_success, log_operation_failed, OperationTimer
    from app.models.training_plan_model import TrainingPlan
    from sqlalchemy import select
    from app.llm.workout_generation.create_workout_service import (
        get_training_history_for_user_from_db,
        format_training_plan_for_llm,
        save_workout_schema_to_db
    )
    from app.llm.workout_generation.workout_generation_chain_v2 import execute_workout_generation_sequence_v2
    from app.llm.utils.db_utils import DatabaseManager

    timer = OperationTimer()
    timer.start()

    db_manager = DatabaseManager()
    
    # ✅ STEP 1: Quick DB operations to gather all necessary data
    try:
        formatted_training_plan = None
        training_plan_db_obj = None
        training_plan_id_for_saving = None
        raw_training_history = None # V2 uses raw history
        
        # DB Session for quick data gathering only
        async with await db_manager.get_session() as db:
            logger.info(f"[generate_workout_background] Loading user data from DB...")
            
            # Load TrainingPlan
            if user_id:
                training_plan_db_obj = await db.scalar(
                    select(TrainingPlan).where(TrainingPlan.user_id == UUID(user_id))
                )
                if training_plan_db_obj:
                    training_plan_id_for_saving = training_plan_db_obj.id
                    formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

                # Load Training History for V2
                raw_training_history = await get_training_history_for_user_from_db(
                    UUID(user_id), db, limit=10
                )
        
        logger.info(f"[generate_workout_background] DB operations completed. Starting LLM generation with V2...")
        
        # ✅ STEP 2: LLM operations using V2 chain WITHOUT any DB connection
        workout_schema = await execute_workout_generation_sequence_v2(
            training_plan_str=formatted_training_plan,
            training_history=raw_training_history,
            user_prompt=request_data.prompt,
            db_manager=db_manager,
        )
        
        logger.info(f"[generate_workout_background] LLM generation completed. Saving to DB...")
        
        # ✅ STEP 3: Quick DB operation to save results
        async with await db_manager.get_session() as save_db:
            updated_workout = await save_workout_schema_to_db(
                db=save_db,
                workout_schema=workout_schema,
                user_id=UUID(user_id),
                training_plan_id=training_plan_id_for_saving,
                workout_id=workout_id
            )
            logger.info(f"[generate_workout_background] Workout saved: {updated_workout.id}")
        
        # ✅ STEP 4: Log success in separate session
        async with await db_manager.get_session() as log_db:
            await log_operation_success(
                db=log_db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )
            
        logger.info(f"[generate_workout_background] Completed successfully in {timer.get_duration_ms()}ms")
            
    except Exception as e:
        logger.error(f"[generate_workout_background] Error: {e}", exc_info=True)
        
        # Separate Session für Error Logging
        try:
            async with await db_manager.get_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms()
                )
        except Exception as log_e:
            logger.error(f"[generate_workout_background] CRITICAL: Failed to log error: {log_e}")


async def revise_workout_background(
    workout_id: int,
    user_id: str,
    request_data: WorkoutRevisionRequestSchema,
    log_id: int
):
    """
    ✅ OPTIMIZED: Background task for workout revision - DB operations separated from LLM calls
    """
    logger.info(f"[revise_workout_background] Starting workout_id: {workout_id}")
    
    from app.db.session import get_background_session
    from app.services.llm_logging_service import log_operation_success, log_operation_failed, OperationTimer
    from app.models.training_plan_model import TrainingPlan
    from sqlalchemy import select
    from app.llm.workout_generation.create_workout_service import (
        format_training_plan_for_llm,
        format_training_history_for_llm
    )
    from app.db.workout_db_access import get_training_history_for_user_from_db
    from app.services.workout_service import get_workout_details
    from app.llm.workout_revision.workout_revision_service import workout_to_dict
    from app.llm.workout_revision.workout_revision_chain import revise_workout_two_step
    
    timer = OperationTimer()
    timer.start()
    
    # ✅ STEP 1: Quick DB operations to gather all necessary data
    try:
        formatted_training_plan = None
        formatted_history = None
        existing_workout_dict = None
        
        # DB Session for quick data gathering only
        async with get_background_session() as db:
            logger.info(f"[revise_workout_background] Loading data from DB...")
            
            # Load TrainingPlan
            training_plan_db_obj = await db.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == UUID(user_id))
            )
            if training_plan_db_obj:
                formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

            # Load Training History
            raw_training_history = await get_training_history_for_user_from_db(
                UUID(user_id), db, limit=10
            )
            if raw_training_history:
                formatted_history = format_training_history_for_llm(raw_training_history)
            
            # Load existing workout
            existing_workout_obj = await get_workout_details(
                workout_id=workout_id,
                db=db
            )
            existing_workout_dict = workout_to_dict(existing_workout_obj)
        
        logger.info(f"[revise_workout_background] DB operations completed. Starting LLM revision...")
        
        # ✅ STEP 2: LLM operations WITHOUT any DB connection (2 LLM calls)
        revised_workout_schema = await revise_workout_two_step(
            existing_workout=existing_workout_dict,
            user_feedback=request_data.user_feedback,
            training_plan=formatted_training_plan,
            training_history=formatted_history
        )
        
        logger.info(f"[revise_workout_background] LLM revision completed. Saving to DB...")
        
        # ✅ STEP 3: Quick DB operation to save results
        async with get_background_session() as save_db:
            # Reload workout object for saving
            existing_workout_obj = await get_workout_details(
                workout_id=workout_id,
                db=save_db
            )
            
            # Store revision as JSON in the revised_workout_data column
            existing_workout_obj.set_revision_data(revised_workout_schema.model_dump())
            
            save_db.add(existing_workout_obj)
            await save_db.commit()
            await save_db.refresh(existing_workout_obj)
            
            logger.info(f"[revise_workout_background] Workout revision saved: {existing_workout_obj.id}")
        
        # ✅ STEP 4: Log success in separate session
        async with get_background_session() as log_db:
            await log_operation_success(
                db=log_db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )
            
        logger.info(f"[revise_workout_background] Completed successfully in {timer.get_duration_ms()}ms")
            
    except Exception as e:
        logger.error(f"[revise_workout_background] Error: {e}", exc_info=True)
        
        # Separate Session für Error Logging
        try:
            async with get_background_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms()
                )
        except Exception as log_e:
            logger.error(f"[revise_workout_background] CRITICAL: Failed to log error: {log_e}")


# ✅ DEPRECATED: Old version - kept for backward compatibility
async def revise_workout_background_old(
    workout_id: int,
    user_id: str,
    request_data: WorkoutRevisionRequestSchema,
    log_id: int
):
    """Background task for workout revision - OLD VERSION (deprecated)"""
    logger.info(f"[revise_workout_background_old] Starting workout_id: {workout_id}")
    
    from app.db.session import get_background_session
    from app.services.llm_logging_service import log_operation_success, log_operation_failed, OperationTimer
    
    timer = OperationTimer()
    timer.start()
    
    try:
        # Use a single session for the entire revision and success logging
        async with get_background_session() as db:
            updated_workout = await run_workout_revision_chain(
                workout_id=workout_id,
                user_feedback=request_data.user_feedback,
                user_id=UUID(user_id),
                db=db,
                save_to_db=True
            )
            logger.info(f"[revise_workout_background_old] Workout revised: {updated_workout.id}")
        
            # Log success within the same transaction
            await log_operation_success(
                db=db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )
            
    except Exception as e:
        logger.error(f"[revise_workout_background_old] Error during workout revision for workout_id {workout_id}: {e}", exc_info=True)
        
        # Use a NEW, separate session to log the failure
        try:
            async with get_background_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms()
                )
        except Exception as log_e:
            logger.error(f"[revise_workout_background_old] CRITICAL: Failed to log error for workout_id {workout_id}: {log_e}", exc_info=True)