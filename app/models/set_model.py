from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .exercise_model import Exercise

class Set(SQLModel, table=True):
    __tablename__ = "sets"
    id: Optional[int] = Field(default=None, primary_key=True)
    exercise_id: int = Field(foreign_key="exercises.id", ondelete="CASCADE")
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    speed: Optional[float] = None
    rest_time: Optional[int] = None
    notes: Optional[str] = None
    
    exercise: "Exercise" = Relationship(back_populates="sets")
