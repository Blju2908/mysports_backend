
from typing import Optional, Dict, Any
from datetime import datetime
import time
import logging
from contextlib import asynccontextmanager
from fastapi import Request, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.llm_call_log_model import LlmCallLog
from app.core.auth import User

logger = logging.getLogger("llm_logging_service")


class LlmCallLogger:
    """
    Service zum Loggen von LLM-bezogenen API-Calls.
    Kann als Context Manager verwendet werden für automatisches Timing und Error-Handling.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        user: User,
        endpoint_name: str,
        method: str = "POST",
        request: Optional[Request] = None,
        llm_operation_type: Optional[str] = None,
        workout_id: Optional[int] = None,
        training_plan_id: Optional[int] = None,
        log_request_data: bool = False
    ):
        self.db = db
        self.user = user
        self.endpoint_name = endpoint_name
        self.method = method
        self.request = request
        self.llm_operation_type = llm_operation_type
        self.workout_id = workout_id
        self.training_plan_id = training_plan_id
        self.log_request_data = log_request_data
        
        self.start_time = None
        self.log_entry = None
        
    async def start_logging(self, request_data: Optional[Dict[str, Any]] = None):
        """Startet das Logging und merkt sich die Startzeit."""
        self.start_time = time.time()
        
        # Client-Informationen extrahieren
        user_agent = None
        ip_address = None
        if self.request:
            user_agent = self.request.headers.get("user-agent")
            ip_address = self.request.client.host if self.request.client else None
        
        # Log-Entry erstellen
        self.log_entry = LlmCallLog(
            user_id=self.user.id,
            endpoint_name=self.endpoint_name,
            method=self.method,
            timestamp=datetime.utcnow(),
            success=False,  # Wird auf True gesetzt wenn erfolgreich
            llm_operation_type=self.llm_operation_type,
            workout_id=self.workout_id,
            training_plan_id=self.training_plan_id,
            user_agent=user_agent,
            ip_address=ip_address,
            request_data=request_data if self.log_request_data else None
        )
        
        logger.info(f"[LLM_LOG] Started {self.endpoint_name} for user {self.user.id}")
    
    async def log_success(
        self, 
        http_status_code: int = 200, 
        response_summary: Optional[str] = None
    ):
        """Loggt einen erfolgreichen Call."""
        if not self.log_entry:
            logger.error("[LLM_LOG] log_success called without start_logging")
            return
            
        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        self.log_entry.success = True
        self.log_entry.http_status_code = http_status_code
        self.log_entry.duration_ms = duration_ms
        self.log_entry.response_summary = response_summary
        
        await self._save_log_entry()
        logger.info(f"[LLM_LOG] Success {self.endpoint_name} for user {self.user.id} in {duration_ms}ms")
    
    async def log_error(
        self, 
        error: Exception, 
        http_status_code: Optional[int] = None
    ):
        """Loggt einen fehlgeschlagenen Call."""
        if not self.log_entry:
            logger.error("[LLM_LOG] log_error called without start_logging")
            return
            
        duration_ms = int((time.time() - self.start_time) * 1000) if self.start_time else None
        
        self.log_entry.success = False
        self.log_entry.duration_ms = duration_ms
        self.log_entry.error_message = str(error)
        self.log_entry.error_type = type(error).__name__
        
        # HTTP Status Code bestimmen
        if isinstance(error, HTTPException):
            self.log_entry.http_status_code = error.status_code
        elif http_status_code:
            self.log_entry.http_status_code = http_status_code
        else:
            self.log_entry.http_status_code = 500
        
        await self._save_log_entry()
        logger.error(f"[LLM_LOG] Error {self.endpoint_name} for user {self.user.id}: {str(error)}")
    
    async def _save_log_entry(self):
        """Speichert den Log-Entry in der Datenbank."""
        try:
            self.db.add(self.log_entry)
            await self.db.commit()
        except Exception as e:
            logger.error(f"[LLM_LOG] Failed to save log entry: {e}")
            await self.db.rollback()


@asynccontextmanager
async def log_llm_call(
    db: AsyncSession,
    user: User,
    endpoint_name: str,
    method: str = "POST",
    request: Optional[Request] = None,
    llm_operation_type: Optional[str] = None,
    workout_id: Optional[int] = None,
    training_plan_id: Optional[int] = None,
    log_request_data: bool = False,
    request_data: Optional[Dict[str, Any]] = None
):
    """
    Context Manager zum automatischen Loggen von LLM-Calls.
    
    Usage:
    async with log_llm_call(db, user, "create_workout", llm_operation_type="workout_creation") as logger:
        # Your LLM operation here
        result = await some_llm_operation()
        await logger.log_success(response_summary="Workout created successfully")
        return result
    """
    call_logger = LlmCallLogger(
        db=db,
        user=user,
        endpoint_name=endpoint_name,
        method=method,
        request=request,
        llm_operation_type=llm_operation_type,
        workout_id=workout_id,
        training_plan_id=training_plan_id,
        log_request_data=log_request_data
    )
    
    await call_logger.start_logging(request_data)
    
    try:
        yield call_logger
    except Exception as e:
        await call_logger.log_error(e)
        raise


# Convenience-Funktionen für häufige Use Cases
async def log_workout_creation(
    db: AsyncSession,
    user: User,
    request: Optional[Request] = None,
    request_data: Optional[Dict[str, Any]] = None
):
    """Context Manager speziell für Workout-Erstellung."""
    return log_llm_call(
        db=db,
        user=user,
        endpoint_name="llm/create-workout",
        llm_operation_type="workout_creation",
        request=request,
        log_request_data=True,
        request_data=request_data
    )


async def log_training_principles_creation(
    db: AsyncSession,
    user: User,
    request: Optional[Request] = None,
    training_plan_id: Optional[int] = None,
    request_data: Optional[Dict[str, Any]] = None
):
    """Context Manager speziell für Training-Principles-Erstellung."""
    return log_llm_call(
        db=db,
        user=user,
        endpoint_name="llm/create-training-principles",
        llm_operation_type="training_principles_creation",
        training_plan_id=training_plan_id,
        request=request,
        log_request_data=True,
        request_data=request_data
    )


async def log_workout_revision(
    db: AsyncSession,
    user: User,
    workout_id: int,
    request: Optional[Request] = None,
    request_data: Optional[Dict[str, Any]] = None
):
    """Context Manager speziell für Workout-Revision."""
    return log_llm_call(
        db=db,
        user=user,
        endpoint_name="workout/revise",
        llm_operation_type="workout_revision",
        workout_id=workout_id,
        request=request,
        log_request_data=True,
        request_data=request_data
    )


async def log_workout_revision_accept(
    db: AsyncSession,
    user: User,
    workout_id: int,
    request: Optional[Request] = None,
    request_data: Optional[Dict[str, Any]] = None
):
    """Context Manager speziell für Workout-Revision-Accept."""
    return log_llm_call(
        db=db,
        user=user,
        endpoint_name="workout/revise/accept",
        llm_operation_type="workout_revision_accept",
        workout_id=workout_id,
        request=request,
        log_request_data=True,
        request_data=request_data
    ) 