from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ExerciseDescriptionRead(BaseModel):
    model_config = {"from_attributes": True}

    name_german: str = Field(description="Deutscher Name als stabiler Primary Key")
    name_english: str
    description_german: str
    difficulty_level: str
    primary_movement_pattern: str
    is_unilateral: bool
    equipment_options: List[str] = []
    target_muscle_groups: List[str] = []
    execution_steps: List[str] = []
    created_at: datetime
    updated_at: datetime 