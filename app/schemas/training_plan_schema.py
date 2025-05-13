from pydantic import BaseModel, field_validator, Field
from typing import Optional, List, Union
from datetime import date, datetime
import logging

logger = logging.getLogger("training_plan")

class TrainingPlanSchema(BaseModel):
    id: Optional[int] = None
    
    # Persönliche Informationen
    gender: Optional[str] = None
    birthdate: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    
    # Trainingsziele
    goal: Optional[str] = None
    goal_type: Optional[str] = None
    goal_details: Optional[str] = None
    
    # Erfahrungslevel
    fitness_level: Optional[int] = None
    experience_level: Optional[int] = None
    
    # Trainingsplan
    training_frequency: Optional[int] = None
    session_duration: Optional[Union[int, str]] = None
    
    # Equipment und Umgebung
    equipment: Optional[str] = None
    equipment_details: Optional[str] = None
    include_cardio: Optional[bool] = None
    
    # Einschränkungen
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    
    # Trainingsprinzipien
    training_principles: Optional[str] = None

    @field_validator('session_duration')
    @classmethod
    def validate_session_duration(cls, value):
        if value is None:
            return None
        if isinstance(value, int):
            return value
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                return 45
        return value

    class Config:
        from_attributes = True

class APIResponse(BaseModel):
    success: bool
    data: Optional[TrainingPlanSchema] = None
    message: str 