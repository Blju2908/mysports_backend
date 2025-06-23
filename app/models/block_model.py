from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .workout_model import Workout
    from .exercise_model import Exercise
    from .set_model import Set

class Block(SQLModel, table=True):
    __tablename__ = "blocks"
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workouts.id", ondelete="CASCADE")
    name: str
    description: Optional[str] = None
    notes: Optional[str] = Field(default=None)
    is_amrap: bool = Field(default=False, description="True, wenn der Block ein AMRAP Block ist.")
    amrap_duration_minutes: Optional[int] = Field(default=None, description="Gesamtdauer des AMRAP-Blocks in Minuten. Nur setzen, wenn is_amrap True ist.")

    workout: "Workout" = Relationship(back_populates="blocks")
    exercises: List["Exercise"] = Relationship(back_populates="block", cascade_delete=True)