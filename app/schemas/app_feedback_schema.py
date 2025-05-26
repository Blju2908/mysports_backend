from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class AppFeedbackCreateSchema(BaseModel):
    """Schema für das Erstellen von neuem App-Feedback"""
    feedback_text: str = Field(..., min_length=10, max_length=2000, description="Feedback-Text des Nutzers")
    wants_response: bool = Field(default=False, description="Möchte der Nutzer eine Antwort erhalten?")

class AppFeedbackSuccessSchema(BaseModel):
    """Einfache Success-Response für Feedback-Erstellung"""
    success: bool = True
    message: str = "Feedback erfolgreich gesendet! Vielen Dank für dein Feedback."
    feedback_id: Optional[int] = None

class AppFeedbackResponseSchema(BaseModel):
    """Schema für die Rückgabe von App-Feedback"""
    id: Optional[int] = None  # Pragmatisch - kann None sein
    user_id: str  # Als String für Frontend-Kompatibilität
    feedback_text: str
    wants_response: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    # Support-Antwort (falls vorhanden)
    response_text: Optional[str] = None
    response_at: Optional[datetime] = None
    responded_by: Optional[str] = None
    
    # Status-Informationen
    status: str
    category: Optional[str] = None
    priority: str
    
    class Config:
        from_attributes = True

class AppFeedbackUpdateSchema(BaseModel):
    """Schema für Support-Team zum Aktualisieren von Feedback"""
    response_text: Optional[str] = Field(None, max_length=2000)
    status: Optional[str] = Field(None)
    category: Optional[str] = None
    priority: Optional[str] = Field(None)
    responded_by: Optional[str] = None

class AppFeedbackListResponseSchema(BaseModel):
    """Schema für Listen-Antworten mit Pagination"""
    feedbacks: list[AppFeedbackResponseSchema]
    total: int
    page: int
    size: int 