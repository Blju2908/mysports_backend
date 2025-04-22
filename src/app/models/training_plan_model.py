from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .training_plan_follower_model import TrainingPlanFollower

if TYPE_CHECKING:
    from .user_model import User
    from .workout_model import Workout

class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: str
    restrictions: str
    equipment: str
    workouts_per_week: int
    session_duration: int
    description: str

    workouts: List["Workout"] = Relationship(back_populates="plan")
    followers: List["User"] = Relationship(back_populates="followed_plans", link_model=TrainingPlanFollower) 