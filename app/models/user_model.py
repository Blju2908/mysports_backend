from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .app_feedback_model import AppFeedbackModel

class UserModel(SQLModel, table=True):
    """
    UserModel dient als Platzhalter für zusätzliche User-Informationen.
    Die Authentifizierung läuft über Supabase (auth.users).
    Die ID entspricht der Supabase-User-ID (UUID).
    """
    
    __tablename__ = "users"
    id: UUID = Field(primary_key=True) # type: ignore
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    # Onboarding Status
    onboarding_completed: bool = Field(default=False)
    
    # Direkte Beziehung zum Trainingsplan (One-to-One)
    training_plan_id: Optional[int] = Field(default=None, foreign_key="training_plans.id")
    training_plan: Optional["TrainingPlan"] = Relationship(back_populates="user")
    
    # Beziehung zu App-Feedback (One-to-Many)
    app_feedback: List["AppFeedbackModel"] = Relationship(back_populates="user")

