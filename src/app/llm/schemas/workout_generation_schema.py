from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from ...models.enums import BlockStatus

class TrainingPlanSchema(BaseModel):
    id: Optional[int]
    goal: str
    restrictions: str
    equipment: str
    workouts_per_week: int
    session_duration: int
    description: str

class ActivityLogSchema(BaseModel):
    id: Optional[int]
    user_id: int
    exercise_name: str
    timestamp: datetime
    weight: Optional[float]
    reps: Optional[int]
    duration: Optional[int]
    notes: Optional[str]

class SetSchema(BaseModel):
    id: Optional[int]
    exercise_id: int
    weight: Optional[float]
    reps: Optional[int]
    duration: Optional[int]
    distance: Optional[float]
    speed: Optional[float]
    rest_time: Optional[int]

class ExerciseSchema(BaseModel):
    id: Optional[int]
    name: str
    description: Optional[str]
    block_id: int
    sets: Optional[List[SetSchema]] = []

class BlockSchema(BaseModel):
    id: Optional[int]
    workout_id: int
    name: str
    description: Optional[str]
    status: BlockStatus
    exercises: Optional[List[ExerciseSchema]] = []

class WorkoutSchema(BaseModel):
    id: Optional[int]
    training_plan_id: Optional[int]
    name: str
    date: datetime
    blocks: Optional[List[BlockSchema]] = [] 