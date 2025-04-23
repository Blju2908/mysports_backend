from pydantic import BaseModel
from typing import Optional

class TrainingPlanResponse(BaseModel):
    id: Optional[int]
    goal: str
    restrictions: str
    equipment: str
    session_duration: int
    description: str

    class Config:
        orm_mode = True

class APIResponse(BaseModel):
    success: bool
    data: Optional[TrainingPlanResponse]
    message: str 