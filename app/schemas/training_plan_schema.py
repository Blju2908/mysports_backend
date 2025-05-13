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
    include_cardio: Optional[str] = None  # 'yes' or 'no'
    
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
        
        # Fix equipment array if it's characters of a PostgreSQL array
        if isinstance(processed_data.get('equipment'), list) and processed_data['equipment']:
            if (len(processed_data['equipment']) > 2 and 
                isinstance(processed_data['equipment'][0], str) and 
                len(processed_data['equipment'][0]) == 1 and
                processed_data['equipment'][0] == '{' and
                processed_data['equipment'][-1] == '}'):
                
                # This looks like a PostgreSQL array that was split into characters
                joined = ''.join(processed_data['equipment'])
                # Remove the PostgreSQL array braces and split by comma
                items = joined[1:-1].split(',')
                processed_data['equipment'] = items
                logger.info(f"Fixed equipment array: {processed_data['equipment']}")
        
        # Fix goal_types array if it's characters of a PostgreSQL array
        if isinstance(processed_data.get('goal_types'), list) and processed_data['goal_types']:
            if (len(processed_data['goal_types']) > 2 and 
                isinstance(processed_data['goal_types'][0], str) and 
                len(processed_data['goal_types'][0]) == 1 and
                processed_data['goal_types'][0] == '{' and
                processed_data['goal_types'][-1] == '}'):
                
                # This looks like a PostgreSQL array that was split into characters
                joined = ''.join(processed_data['goal_types'])
                # Remove the PostgreSQL array braces and split by comma
                items = joined[1:-1].split(',')
                processed_data['goal_types'] = items
                logger.info(f"Fixed goal_types array: {processed_data['goal_types']}")
        
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
        # No conversion needed as model now matches frontend format
        return self.model_dump(exclude_none=True)

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None