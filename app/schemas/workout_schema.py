from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.set_model import SetStatus # For SetResponseSchema
# No BlockStatus as it was removed from block_model

# Base Schemas for individual models - ensuring consistency with DB models

class SetBaseSchema(BaseModel):
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    
    # Common values
    rest_time: Optional[int] = None  # in seconds
    
    # Status tracking
    status: SetStatus = Field(default=SetStatus.open)
    completed_at: Optional[datetime] = None

class SetResponseSchema(SetBaseSchema):
    id: int
    exercise_id: int
    
    class Config:
        from_attributes = True

class ExerciseBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None

class ExerciseResponseSchema(ExerciseBaseSchema):
    id: int
    block_id: int
    sets: List[SetResponseSchema] = []
    
    class Config:
        from_attributes = True

class BlockBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None

class BlockResponseSchema(BlockBaseSchema):
    id: int
    workout_id: int
    exercises: List[ExerciseResponseSchema] = []
    
    class Config:
        from_attributes = True

class WorkoutBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    duration: Optional[int] = None 
    focus: Optional[str] = None 
    notes: Optional[str] = None

class WorkoutResponseSchema(WorkoutBaseSchema):
    id: int
    training_plan_id: Optional[int] = None # from workout_model
    date_created: datetime # from workout_model
    class Config:
        from_attributes = True

# Schema for workout details including blocks, exercises, and sets
class WorkoutSchemaWithBlocks(WorkoutResponseSchema): # Inherits from WorkoutResponseSchema
    blocks: List[BlockResponseSchema] = []
    
    class Config:
        from_attributes = True
