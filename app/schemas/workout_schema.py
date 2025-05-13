from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Response Schemas
class WorkoutResponseSchema(BaseModel):
    id: int
    name: str
    date: datetime
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

# Schema for workout details with blocks and exercises
class SetResponseSchema(BaseModel):
    id: Optional[int] = None
    exercise_id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
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
    exercises: List[ExerciseResponseSchema] = []
    
    class Config:
        from_attributes = True

class WorkoutSchemaWithBlocks(WorkoutResponseSchema):
    blocks: List[BlockResponseSchema] = []
    
    class Config:
        from_attributes = True

# --- Input Schemas for Saving Activity Block ---

class ActivitySetSchema(BaseModel):
    id: int # Set ID from the original plan
    exercise_name: str # Name of the exercise for context
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None # Assuming duration in seconds
    distance: Optional[float] = None # Assuming distance in km
    speed: Optional[float] = None # Assuming speed in km/h
    rest_time: Optional[int] = None # Assuming rest time in seconds
    notes: Optional[str] = None # Kept the uncommented line
    # notes: Optional[str] = None # If frontend can send notes -> This line was removed by the edit. Will remove manually if still present

class ActivityBlockPayloadSchema(BaseModel):
    block_id: int
    workout_id: int  # Neu: Workout-ID für die Verknüpfung
    sets: List[ActivitySetSchema] 