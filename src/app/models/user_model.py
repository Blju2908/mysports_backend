from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .training_history import ActivityLog

class UserModel(SQLModel, table=True):
    """
    UserModel dient als Platzhalter für zusätzliche User-Informationen.
    Die Authentifizierung läuft über Supabase (auth.users).
    Die ID entspricht der Supabase-User-ID (UUID).
    """
    __tablename__ = "users"
    id: UUID = Field(primary_key=True)
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None

    # Beziehungen zu anderen Modellen
    followed_plans: List["TrainingPlan"] = Relationship(back_populates="followers")
    activity_log: List["ActivityLog"] = Relationship(back_populates="user")