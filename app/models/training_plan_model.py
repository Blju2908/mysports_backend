from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workout_model import Workout


class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: Optional[str] = Field(default=None)
    restrictions: Optional[str] = Field(default=None)
    equipment: Optional[str] = Field(default=None)
    session_duration: Optional[int] = Field(default=None)

    # Direkte Beziehung zum User (One-to-One)
    user: Optional["UserModel"] = Relationship(back_populates="training_plan")
    
    # Beziehung zu Workouts
    workouts: List["Workout"] = Relationship(back_populates="plan")
