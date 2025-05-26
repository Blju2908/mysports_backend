from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field, JSON, Column
from sqlalchemy import Text
import uuid


class LlmCallLog(SQLModel, table=True):
    """
    Model zum Tracken aller LLM-bezogenen API-Aufrufe.
    Ermöglicht Monitoring von Nutzung, Erfolgsraten und Debugging.
    """
    __tablename__ = "llm_call_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # User-Informationen
    user_id: str = Field(description="UUID des Users der den Call gemacht hat")
    
    # Call-Informationen
    endpoint_name: str = Field(description="Name des aufgerufenen Endpoints")
    method: str = Field(default="POST", description="HTTP-Method (GET, POST, etc.)")
    
    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Zeitstempel des API-Calls")
    duration_ms: Optional[int] = Field(default=None, description="Dauer des Calls in Millisekunden")
    
    # Status
    success: bool = Field(description="Ob der Call erfolgreich war")
    http_status_code: Optional[int] = Field(default=None, description="HTTP Status Code der Response")
    
    # Error-Informationen
    error_message: Optional[str] = Field(default=None, sa_column=Column(Text), description="Fehlernachricht falls vorhanden")
    error_type: Optional[str] = Field(default=None, description="Typ des Fehlers (HTTPException, ValueError, etc.)")
    
    # Request/Response Data (optional für Debugging)
    request_data: Optional[dict] = Field(default=None, sa_column=Column(JSON), description="Request-Daten (optional)")
    response_summary: Optional[str] = Field(default=None, sa_column=Column(Text), description="Zusammenfassung der Response")
    
    # LLM-spezifische Informationen
    llm_operation_type: Optional[str] = Field(default=None, description="Art der LLM-Operation (workout_creation, revision, etc.)")
    workout_id: Optional[int] = Field(default=None, description="Workout ID falls relevant")
    training_plan_id: Optional[int] = Field(default=None, description="Training Plan ID falls relevant")
    
    # Metadaten
    user_agent: Optional[str] = Field(default=None, description="User Agent des Clients")
    ip_address: Optional[str] = Field(default=None, description="IP-Adresse des Clients")
    
    class Config:
        from_attributes = True 