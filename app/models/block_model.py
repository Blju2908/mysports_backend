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
    duration_min: Optional[int] = Field(default=None, description="Estimated duration of the block in minutes")
    
    # Ordering
    position: Optional[int] = Field(default=0, description="Position for stable sorting of blocks within a workout")

    workout: "Workout" = Relationship(back_populates="blocks")
    exercises: List["Exercise"] = Relationship(back_populates="block", cascade_delete=True, sa_relationship_kwargs={"order_by": "Exercise.position"})