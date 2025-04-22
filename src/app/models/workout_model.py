from typing import Optional, List, TYPE_CHECKING
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .block_model import Block

class Workout(SQLModel, table=True):
    __tablename__ = "workouts"

    id: Optional[int] = Field(default=None, primary_key=True)
    training_plan_id: Optional[int] = Field(default=None, foreign_key="training_plans.id")
    name: str
    date: datetime

    plan: Optional["TrainingPlan"] = Relationship(back_populates="workouts")
    blocks: List["Block"] = Relationship(back_populates="workout")