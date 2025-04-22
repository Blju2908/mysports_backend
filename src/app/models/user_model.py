from typing import Optional, List, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship
from .training_plan_follower_model import TrainingPlanFollower

if TYPE_CHECKING:
    from .training_plan_model import TrainingPlan
    from .training_history import ActivityLog

class User(SQLModel, table=True):
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    email: str
    hashed_password: str
    is_active: bool = True
    followed_plans: List["TrainingPlan"] = Relationship(
        back_populates="followers", link_model=TrainingPlanFollower
    )
    activity_log: List["ActivityLog"] = Relationship(back_populates="user")