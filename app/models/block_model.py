from typing import Optional, List, TYPE_CHECKING
from enum import Enum
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .workout_model import Workout
    from .exercise_model import Exercise
    from .set_model import Set

class BlockStatus(str, Enum):
    open = "open"
    done = "done"

class Block(SQLModel, table=True):
    __tablename__ = "blocks"
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workouts.id", ondelete="CASCADE")
    name: str
    description: Optional[str] = None
    status: BlockStatus = Field(default=BlockStatus.open, sa_column_kwargs={"nullable": False})

    workout: "Workout" = Relationship(back_populates="blocks")
    exercises: List["Exercise"] = Relationship(back_populates="block", cascade_delete=True)