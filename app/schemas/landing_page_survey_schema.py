from pydantic import BaseModel, EmailStr
from typing import List, Optional
from datetime import datetime

class LandingPageSurveyCreateSchema(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    training_goals: Optional[List[str]] = []
    training_types: Optional[List[str]] = []
    current_apps: Optional[List[str]] = []
    comment: Optional[str] = None
    price_willingness: Optional[str] = None

class LandingPageSurveyResponseSchema(BaseModel):
    id: int
    email: str
    name: Optional[str]
    training_goals: Optional[List[str]]
    training_types: Optional[List[str]]
    current_apps: Optional[List[str]]
    comment: Optional[str]
    price_willingness: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True

class LandingPageSurveySuccessSchema(BaseModel):
    success: bool
    message: str
    survey_id: Optional[int] = None 