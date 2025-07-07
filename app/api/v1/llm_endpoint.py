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
        await db.commit()
        await db.refresh(placeholder_workout)
        
        workout_id = placeholder_workout.id
        logger.info("[llm/start-workout] Placeholder-Workout erstellt mit ID: %s", workout_id)
        
        # ✅ NEU: Erstelle sofort Log-Eintrag mit Status STARTED
        log_id = await log_operation_start(
            db=db,
            user_id=current_user.id,
            endpoint_name="llm/start-workout-creation",
            llm_operation_type="workout_creation",
            workout_id=workout_id
        )
        
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
    ✅ IMPROVED: Background-Task für die asynchrone Workout-Generierung.
    Nutzt dedizierte Session-Erstellung für Background Tasks.
    """
    logger.info("[generate_workout_background] Start für workout_id: %s, log_id: %s", workout_id, log_id)
    
    # Timer für Performance-Messung
    timer = OperationTimer()
    timer.start()
    
    # ✅ IMPROVED: Nutze dedizierte Background Session (sauberer als async for + break)
    from app.db.session import create_background_session
    
    async with create_background_session() as db:
        try:
            # ✅ Direkte Workout-Generierung mit sauberer Session-Verwaltung
            updated_workout = await run_workout_chain(
                user_id=UUID(user_id),
                user_prompt=request_data.prompt,
                db=db,
                save_to_db=True,
                use_exercise_filtering=request_data.use_exercise_filtering,
                workout_id=workout_id
            )
            
            logger.info("[generate_workout_background] Workout erfolgreich aktualisiert: %s", updated_workout.id)
            
            # ✅ Update bestehenden Log-Eintrag mit SUCCESS
            await log_operation_success(
                db=db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )
                
        except Exception as e:
            logger.error("[generate_workout_background] Exception: %s", str(e), exc_info=True)
            
            # ✅ Update bestehenden Log-Eintrag mit FAILED
            await log_operation_failed(
                db=db,
                log_id=log_id,
                error_message=str(e),
                duration_ms=timer.get_duration_ms()
            )
            
            # Bei Fehler: Placeholder-Workout löschen (mit Rollback-Sicherheit)
            try:
                stmt = select(Workout).where(Workout.id == workout_id)
                result = await db.execute(stmt)
                workout = result.scalar_one_or_none()
                if workout:
                    await db.delete(workout)
                    await db.commit()
                    logger.info("[generate_workout_background] Placeholder-Workout gelöscht")
            except Exception as cleanup_error:
                logger.error("[generate_workout_background] Cleanup error: %s", str(cleanup_error))
                await db.rollback()  # ✅ IMPROVED: Explicit rollback bei Cleanup-Fehlern


async def revise_workout_background(
    workout_id: int,
    user_id: str,
    request_data: WorkoutRevisionRequestSchema,
    log_id: int
):
    """
    ✅ REFACTORED: Background-Task für die asynchrone Workout-Revision.
    Nutzt den neuen Service mit atomischem DB-Update.
    """
    logger.info("[revise_workout_background] Start für workout_id: %s, log_id: %s", workout_id, log_id)
    
    # Timer für Performance-Messung
    timer = OperationTimer()
    timer.start()
    
    from app.db.session import create_background_session
    
    async with create_background_session() as db:
        try:
            # ✅ NEW: Nutze den refactored Service mit atomischem DB-Update
            updated_workout = await run_workout_revision_chain(
                workout_id=workout_id,
                user_feedback=request_data.user_feedback,
                user_id=UUID(user_id),
                db=db,
                save_to_db=True
            )
            
            logger.info("[revise_workout_background] Workout-Revision erfolgreich abgeschlossen: %s", updated_workout.id)
            
            # ✅ Update bestehenden Log-Eintrag mit SUCCESS
            await log_operation_success(
                db=db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )
                
        except Exception as e:
            logger.error("[revise_workout_background] Exception: %s", str(e), exc_info=True)
            
            # ✅ Update bestehenden Log-Eintrag mit FAILED
            await log_operation_failed(
                db=db,
                log_id=log_id,
                error_message=str(e),
                duration_ms=timer.get_duration_ms()
            )