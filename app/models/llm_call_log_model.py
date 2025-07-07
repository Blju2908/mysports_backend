from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field
from enum import Enum


class LlmOperationStatus(str, Enum):
    """Status einer LLM-Operation - klar und eindeutig"""
    STARTED = "started"
    SUCCESS = "success" 
    FAILED = "failed"


class LlmCallLog(SQLModel, table=True):
    """
    Minimales, fokussiertes Model zum Tracken von LLM-Operationen.
    Nur die wirklich benötigten Felder für Monitoring und Debugging.
    """
    __tablename__ = "llm_call_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Kern-Identifikation
    user_id: str = Field(description="UUID des Users der die Operation ausgelöst hat")
    endpoint_name: str = Field(description="Name des API-Endpoints (z.B. 'llm/create-workout')")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Zeitstempel des Starts")
    duration_ms: Optional[int] = Field(default=None, description="Dauer der Operation in Millisekunden")
    
    # Status-Tracking (Optional für bestehende Datensätze)
    status: Optional[LlmOperationStatus] = Field(default=None, description="Aktueller Status der Operation")
    
    # Error-Handling
    error_message: Optional[str] = Field(default=None, description="Fehlermeldung bei gescheiterten Operationen")
    
    # Business-Kontext
    llm_operation_type: str = Field(description="Art der Operation: workout_creation, workout_revision, workout_status_check")
    workout_id: Optional[int] = Field(default=None, description="Workout ID falls relevant für die Operation")
    
    class Config:
        from_attributes = True 