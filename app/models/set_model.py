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
    plan_weight: Optional[float] = None
    plan_reps: Optional[int] = None
    plan_duration: Optional[int] = None  # in seconds
    plan_distance: Optional[float] = None
    plan_speed: Optional[float] = None
    
    # Execution values
    execution_weight: Optional[float] = None
    execution_reps: Optional[int] = None
    execution_duration: Optional[int] = None  # in seconds
    execution_distance: Optional[float] = None
    execution_speed: Optional[float] = None
    
    # Common values
    rest_time: Optional[int] = None  # in seconds
    notes: Optional[str] = None
    
    # Status tracking
    status: SetStatus = Field(default=SetStatus.open)
    completed_at: Optional[datetime] = None
    
    exercise: "Exercise" = Relationship(back_populates="sets")
