from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .enums import BlockStatus

if TYPE_CHECKING:
    from .workout_model import Workout
    from .exercise_model import Exercise
    from .set_model import Set
class Block(SQLModel, table=True):
    __tablename__ = "blocks"
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workouts.id")
    name: str
    description: Optional[str] = None
    status: BlockStatus

    workout: "Workout" = Relationship(back_populates="blocks")
    exercises: List["Exercise"] = Relationship(back_populates="block")