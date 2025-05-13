from pydantic import BaseModel
from typing import Optional

class TrainingPlanSchema(BaseModel):
    id: Optional[int] = None
    goal: str
    restrictions: str
    equipment: str
    session_duration: Optional[int] = None

    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    success: bool
    data: Optional[TrainingPlanSchema]
    message: str 