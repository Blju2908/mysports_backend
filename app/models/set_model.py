from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING
from enum import Enum
from datetime import datetime

if TYPE_CHECKING:
    from .exercise_model import Exercise

class SetStatus(str, Enum):
    open = "open"
    done = "done"

class Set(SQLModel, table=True):
    __tablename__ = "sets"
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="exercises.id", ondelete="CASCADE")
    
    # Planned values
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    
    # Common values
    rest_time: Optional[int] = None  # in seconds
    
    # Status tracking
    status: SetStatus = Field(default=SetStatus.open)
    completed_at: Optional[datetime] = None
    
    
    exercise: "Exercise" = Relationship(back_populates="sets")
