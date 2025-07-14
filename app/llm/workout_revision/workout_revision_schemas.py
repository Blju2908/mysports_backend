from pydantic import BaseModel, Field
from typing import Optional
from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema


class WorkoutRevisionRequestSchema(BaseModel):
    """Schema for workout revision requests."""
    workout_id: int = Field(..., description="ID des zu überarbeitenden Workouts")
    user_feedback: str = Field(..., description="Feedback/Kommentar des Users zur gewünschten Änderung")
    training_plan: Optional[str] = Field(default=None, description="Optionaler Trainingsplan als Kontext")
    training_history: Optional[str] = Field(default=None, description="Optionale Trainingshistorie als JSON-String")


class WorkoutRevisionResponseSchema(BaseModel):
    """Schema for workout revision responses."""
    original_workout_id: int = Field(..., description="ID des ursprünglichen Workouts")
    user_feedback: str = Field(..., description="Das User-Feedback, das verwendet wurde")
    revised_workout: CompactWorkoutSchema = Field(..., description="Das überarbeitete Workout")
    revision_timestamp: str = Field(..., description="Zeitstempel der Überarbeitung")


class WorkoutRevisionPreviewSchema(BaseModel):
    """Schema for workout revision preview (before confirmation)."""
    revised_workout: CompactWorkoutSchema = Field(..., description="Das überarbeitete Workout (Vorschau)")
    changes_summary: Optional[str] = Field(default=None, description="Zusammenfassung der Änderungen")


class WorkoutRevisionConfirmationSchema(BaseModel):
    """Schema for confirming a workout revision."""
    confirm: bool = Field(..., description="Bestätigung der Überarbeitung")
    save_as_new: bool = Field(default=False, description="Als neues Workout speichern statt überschreiben")
    new_workout_name: Optional[str] = Field(default=None, description="Name für das neue Workout (falls save_as_new=True)") 