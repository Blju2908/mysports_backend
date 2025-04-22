from sqlmodel import SQLModel, Field

class TrainingPlanFollower(SQLModel, table=True):
    __tablename__ = "training_plan_followers"
    user_id: int = Field(foreign_key="users.id", primary_key=True)
    training_plan_id: int = Field(foreign_key="training_plans.id", primary_key=True) 