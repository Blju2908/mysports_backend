from typing import Optional, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID
import sqlalchemy as sa

if TYPE_CHECKING:
    from .user_model import UserModel

class AppFeedbackModel(SQLModel, table=True):
    """
    Model für allgemeines App-Feedback von Nutzern.
    Speichert Feedback-Text, Datum und ob eine Antwort erwünscht ist.
    """
    
    __tablename__ = "app_feedback"
    
    id: Optional[int] = Field(
        default=None, 
        primary_key=True,
        sa_column_kwargs={"autoincrement": True}
    )
    user_id: UUID = Field(foreign_key="users.id")
    feedback_text: str = Field(min_length=10, max_length=2000)
    wants_response: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Optional: Antwort vom Support-Team
    response_text: Optional[str] = Field(default=None, max_length=2000)
    response_at: Optional[datetime] = None
    responded_by: Optional[str] = None  # Name/ID des Support-Mitarbeiters
    
    # Status für interne Verwaltung
    status: str = Field(default="open")  # open, in_progress, closed
    category: Optional[str] = None  # bug, feature_request, general, etc.
    priority: str = Field(default="normal")  # low, normal, high, urgent
    
    # Beziehung zum User
    user: Optional["UserModel"] = Relationship(back_populates="app_feedback") 