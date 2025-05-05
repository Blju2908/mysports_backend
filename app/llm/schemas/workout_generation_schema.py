from pydantic import BaseModel, Field
from typing import List

class SetSchema(BaseModel):
    values: List[float] = Field(..., description="Werte in der Reihenfolge: [weight, reps, duration, distance, speed, rest_time]. Bei nicht relevanten Werten bitte null eintragen.")

class ExerciseSchema(BaseModel):
    name: str
    description: str
    sets: List[SetSchema]

class BlockSchema(BaseModel):
    name: str
    description: str
    exercises: List[ExerciseSchema]

class WorkoutSchema(BaseModel):
    training_plan_id: int
    name: str
    description: str
    blocks: List[BlockSchema]