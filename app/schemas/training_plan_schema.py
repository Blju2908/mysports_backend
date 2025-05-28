# backend/app/schemas/training_plan_schema.py
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Union, Dict, Any
from datetime import date
import logging

logger = logging.getLogger(__name__)

class TrainingPlanSchema(BaseModel):
    id: Optional[int] = None
    
    # Personal Info
    gender: Optional[str] = None
    birthdate: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    
    # Training Goals
    goal_types: Optional[List[str]] = Field(default_factory=list)
    goal_details: Optional[str] = None
    
    # Experience & Fitness
    fitness_level: Optional[int] = None
    experience_level: Optional[int] = None
    
    # Training Schedule
    training_frequency: Optional[int] = None
    session_duration: Optional[Union[str, int]] = None
    
    # Equipment & Environment
    equipment: Optional[List[str]] = Field(default_factory=list)
    equipment_details: Optional[str] = None
    include_cardio: Optional[bool] = None  
    
    # Restrictions & Limitations
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    
    # Training Principles (AI-generated)
    training_principles: Optional[str] = None
    training_principles_json: Optional[Dict[str, Any]] = None
    
    @field_validator('birthdate', mode='before')
    @classmethod
    def parse_birthdate(cls, v):
        """Parse birthdate from various formats"""
        if v is None:
            return None
        if isinstance(v, date):
            return v
        if isinstance(v, str):
            try:
                # Parse ISO format date string (YYYY-MM-DD)
                year, month, day = v.split('-')
                return date(int(year), int(month), int(day))
            except (ValueError, TypeError) as e:
                logger.error(f"Error parsing birthdate '{v}': {e}")
                return None
        return v
    
    @classmethod
    def from_frontend_format(cls, data: Dict[str, Any]) -> "TrainingPlanSchema":
        """Convert frontend data to schema format"""
        # Pydantic handles the validation automatically with field_validator
        return cls(**data)
    
    def to_frontend_format(self) -> Dict[str, Any]:
        """Convert schema to frontend format with proper date serialization"""
        result = self.model_dump(exclude_none=True)
        
        # Ensure arrays are always arrays (never None)
        if result.get('goal_types') is None:
            result['goal_types'] = []
        if result.get('equipment') is None:
            result['equipment'] = []
            
        return result

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None