from typing import Optional, Dict, Any
from datetime import datetime
import time
import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_call_log_model import LlmCallLog, LlmOperationStatus

logger = logging.getLogger("llm_logging_service")


async def log_operation_start(
    db: AsyncSession,
    user_id: str,
    endpoint_name: str,
    llm_operation_type: str,
    workout_id: Optional[int] = None
) -> int:
    """
    Loggt den Start einer LLM-Operation.
    
    Returns:
        log_id: ID des erstellten Log-Eintrags für spätere Updates
    """
    log_entry = LlmCallLog(
        user_id=user_id,
        endpoint_name=endpoint_name,
        timestamp=datetime.utcnow(),
        status=LlmOperationStatus.STARTED,
        llm_operation_type=llm_operation_type,
        workout_id=workout_id
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    logger.info(f"[LLM_LOG] Started {endpoint_name} for user {user_id} (log_id: {log_entry.id})")
    return log_entry.id


async def log_operation_success(
    db: AsyncSession,
    log_id: int,
    duration_ms: Optional[int] = None
):
    """Markiert eine Operation als erfolgreich."""
    log_entry = await db.get(LlmCallLog, log_id)
    if not log_entry:
        logger.error(f"[LLM_LOG] Log entry {log_id} not found for success update")
        return
    
    log_entry.status = LlmOperationStatus.SUCCESS
    log_entry.duration_ms = duration_ms
    log_entry.error_message = None  # Clear any previous error
    
    await db.commit()
    logger.info(f"[LLM_LOG] Success operation {log_id} completed in {duration_ms}ms")


async def log_operation_failed(
    db: AsyncSession,
    log_id: int,
    error_message: str,
    duration_ms: Optional[int] = None
):
    """Markiert eine Operation als fehlgeschlagen."""
    log_entry = await db.get(LlmCallLog, log_id)
    if not log_entry:
        logger.error(f"[LLM_LOG] Log entry {log_id} not found for error update")
        return
    
    log_entry.status = LlmOperationStatus.FAILED
    log_entry.duration_ms = duration_ms
    log_entry.error_message = error_message
    
    await db.commit()
    logger.error(f"[LLM_LOG] Failed operation {log_id}: {error_message}")


# ✅ NEW: Workout Revision specific logging functions
async def log_workout_revision_start(
    db: AsyncSession,
    user_id: str,
    workout_id: int,
    request_data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Startet das Logging für eine Workout-Revision.
    
    Returns:
        log_id: ID des erstellten Log-Eintrags für spätere Updates
    """
    return await log_operation_start(
        db=db,
        user_id=user_id,
        endpoint_name="llm/start-workout-revision",
        llm_operation_type="workout_revision",
        workout_id=workout_id
    )


async def log_workout_revision_accept(
    db: AsyncSession,
    user_id: str,
    workout_id: int,
    request_data: Optional[Dict[str, Any]] = None
) -> int:
    """
    Loggt eine synchrone Workout-Revision-Accept Operation.
    
    Returns:
        log_id: ID des erstellten Log-Eintrags
    """
    log_entry = LlmCallLog(
        user_id=user_id,
        endpoint_name="llm/accept-workout-revision",
        timestamp=datetime.utcnow(),
        status=LlmOperationStatus.SUCCESS,  # Direkt als erfolgreich markieren
        llm_operation_type="workout_revision_accept",
        workout_id=workout_id,
        duration_ms=0  # Synchrone Operation, sehr schnell
    )
    
    db.add(log_entry)
    await db.commit()
    await db.refresh(log_entry)
    
    logger.info(f"[LLM_LOG] Workout revision accepted for user {user_id}, workout {workout_id} (log_id: {log_entry.id})")
    return log_entry.id


# Helper-Klasse für Timing
class OperationTimer:
    """Einfache Timer-Klasse für Performance-Messung."""
    
    def __init__(self):
        self.start_time = None
    
    def start(self):
        """Startet den Timer."""
        self.start_time = time.time()
    
    def get_duration_ms(self) -> Optional[int]:
        """Gibt die Dauer in Millisekunden zurück."""
        if self.start_time is None:
            return None
        return int((time.time() - self.start_time) * 1000)