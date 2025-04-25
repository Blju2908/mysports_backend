from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.models.workout_model import WorkoutStatus
from app.models.block_model import BlockStatus

# Response Schemas
class WorkoutResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime
    description: Optional[str] = None
    status: WorkoutStatus
    
    class Config:
        from_attributes = True

# Schema for workout details with blocks and exercises
class SetResponseSchema(BaseModel):
    id: Optional[int] = None
    exercise_id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    speed: Optional[float] = None
    rest_time: Optional[int] = None
    
    class Config:
        from_attributes = True

class ExerciseResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    block_id: int
    sets: List[SetResponseSchema] = []
    
    class Config:
        from_attributes = True

class BlockResponseSchema(BaseModel):
    id: int
    workout_id: int
    name: str
    description: Optional[str] = None
    status: BlockStatus
    exercises: List[ExerciseResponseSchema] = []
    
    class Config:
        from_attributes = True

class WorkoutDetailResponseSchema(WorkoutResponseSchema):
    blocks: List[BlockResponseSchema] = []
    
    class Config:
        from_attributes = True

# --- Input Schemas for Saving Activity Block ---

class ActivitySetSchema(BaseModel):
    # Include fields expected from frontend that map to ActivityLog
    id: Optional[int] # The ID of the original Set
    exercise_id: int
    exercise_name: str # Expecting frontend to send this based on step data
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    speed: Optional[float] = None
    rest_time: Optional[int] = None
    # notes: Optional[str] = None # If frontend can send notes

class ActivityBlockPayloadSchema(BaseModel):
    sets: List[ActivitySetSchema] 