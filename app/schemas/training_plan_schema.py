# 1. Update backend/app/schemas/training_plan_schema.py
from pydantic import BaseModel, Field
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
    goal_types: Optional[List[str]] = None
    goal_details: Optional[str] = None
    
    # Experience & Fitness
    fitness_level: Optional[int] = None
    experience_level: Optional[int] = None
    
    # Training Schedule
    training_frequency: Optional[int] = None
    session_duration: Optional[Union[str, int]] = None
    
    # Equipment & Environment
    equipment: Optional[List[str]] = None
    equipment_details: Optional[str] = None
    include_cardio: Optional[bool] = None  
    
    # Restrictions & Limitations
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    
    # Training Principles (AI-generated)
    training_principles: Optional[str] = None
    
    # Simplified conversion methods
    @classmethod
    def from_frontend_format(cls, data: Dict[str, Any]) -> "TrainingPlanSchema":
        # Create a copy to avoid modifying the original
        processed_data = dict(data)
        
        # Handle birthdate
        if 'birthdate' in processed_data and isinstance(processed_data['birthdate'], str):
            try:
                # Parse ISO format date string
                year, month, day = processed_data['birthdate'].split('-')
                processed_data['birthdate'] = date(int(year), int(month), int(day))
                logger.info(f"Converted birthdate string to date: {processed_data['birthdate']}")
            except (ValueError, TypeError) as e:
                logger.error(f"Error converting birthdate: {e}")
                # Keep as string if conversion fails
                pass
        
        return cls(**processed_data)
    
    def to_frontend_format(self) -> Dict[str, Any]:
        # Convert to dict
        result = self.model_dump(exclude_none=True)
        
        return result

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None