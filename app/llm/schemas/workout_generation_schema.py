from pydantic import BaseModel, Field
from typing import Optional, List

class SetSchema(BaseModel):
    id: int
    exercise_id: int
    weight: Optional[float]
    reps: Optional[int]
    duration: Optional[int]
    distance: Optional[float]
    speed: Optional[float]
    rest_time: Optional[int]

class ExerciseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = Field(None, description="Schlagworte zur Durchführung (1 Satz) - wiederhole aber nicht die Anzahl der Sätze, das Gewicht und die Pausenzeiten. Nenne angesprochene Muskeln bzw. Zielsetzung der Übung")
    block_id: int
    sets: Optional[List[SetSchema]] = None

class BlockSchema(BaseModel):
    id: int
    workout_id: int
    name: str
    description: Optional[str] = Field(None, description="Zielsetzung des Blocks in Schlagworten")
    exercises: Optional[List[ExerciseSchema]] = None

class WorkoutSchema(BaseModel):
    id: Optional[int]
    training_plan_id: Optional[int]
    name: str
    description: str = Field(..., description="Schwerpunkt des Workouts in Schlagworten")
    blocks: Optional[List[BlockSchema]] = None 