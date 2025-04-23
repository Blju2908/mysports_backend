from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
from .training_plan_follower_model import TrainingPlanFollower

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workout_model import Workout


class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: str
    restrictions: str
    equipment: str
    session_duration: int
    description: str

    # followers verweist auf UserModel mit Supabase-User-ID (UUID)
    followers: List["UserModel"] = Relationship(
        back_populates="followed_plans", link_model=TrainingPlanFollower
    )
    workouts: List["Workout"] = Relationship(back_populates="plan")
