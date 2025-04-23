from sqlmodel import SQLModel, Field
from uuid import UUID

class TrainingPlanFollower(SQLModel, table=True):
    __tablename__ = "training_plan_followers"
    # user_id ist die Supabase-User-ID (UUID)
    user_id: UUID = Field(foreign_key="users.id", primary_key=True, ondelete="CASCADE")
    training_plan_id: int = Field(foreign_key="training_plans.id", primary_key=True, ondelete="CASCADE") 