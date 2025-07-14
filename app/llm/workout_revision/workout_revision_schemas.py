from pydantic import BaseModel, Field
from typing import Optional
from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema


class WorkoutRevisionRequestSchema(BaseModel):
    """Schema for workout revision requests (V2 - Simplified)."""
    workout_id: int = Field(..., description="ID des zu überarbeitenden Workouts")
    user_feedback: str = Field(..., description="Feedback/Kommentar des Users zur gewünschten Änderung")
    # Note: training_plan and training_history are automatically loaded from the database
    # in V2, so they are no longer part of the request schema


