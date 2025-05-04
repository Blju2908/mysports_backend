from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

if TYPE_CHECKING:
    from .user_model import UserModel

class ActivityLog(SQLModel, table=True):
    __tablename__ = "training_history"
    id: Optional[int] = Field(default=None, primary_key=True)
    # user_id ist die Supabase-User-ID (UUID)
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    exercise_name: str = Field(nullable=False)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    set_id: Optional[int] = Field(default=None, foreign_key="sets.id", ondelete="SET NULL")
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # Sekunden
    distance: Optional[float] = None
    speed: Optional[float] = None
    rest_time: Optional[int] = None  # Sekunden
    notes: Optional[str] = None  # Freitext für Bemerkungen
    user: "UserModel" = Relationship(back_populates="activity_log")
