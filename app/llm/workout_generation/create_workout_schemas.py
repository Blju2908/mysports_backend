from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union

class SetSchema(BaseModel):
    reps: Optional[int] = Field(None, description="Anzahl der Wiederholungen.")
    duration_seconds: Optional[int] = Field(None, description="Dauer der Übung in Sekunden.")
    weight: Optional[float] = Field(None, description="Gewicht in Kilogramm für die Übung.")
    distance: Optional[float] = Field(None, description="Distanz in Metern für die Übung.")
    rest_seconds: Optional[int] = Field(None, description="Pause nach dem Satz in Sekunden.")

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung.")
    sets: List[SetSchema] = Field(..., description="Liste der Sätze für diese Übung.")
    superset_id: Optional[str] = Field(default=None, description="Eindeutige ID für Supersets. Übungen mit derselben superset_id werden abwechselnd ausgeführt (z.B. 'A', 'B', 'C'). Null für normale Übungen ohne Superset.")
    position: int = Field(default=0, description="Position der Übung in dem Block.")

class BlockSchema(BaseModel):
    name: str = Field(..., description="Name des Workout-Blocks (z.B. Aufwärmen, Hauptteil, Cooldown).")
    description: str = Field(..., description="Beschreibung des Blocks.")
    exercises: List[ExerciseSchema] = Field(..., description="Liste der Übungen in diesem Block.")
    position: int = Field(default=0, description="Position des Blocks in dem Workout.")
    
class WorkoutSchema(BaseModel):
    name: str = Field(..., description="Name des Workouts. z.B. 'Push-Training'")
    description: str = Field(..., description="Kurze Beschreibung des gesamten Workouts.")
    duration: int = Field(..., description="Dauer des Workouts in Minuten.")
    focus: str = Field(..., description="Hauptfokus des Workouts in max. 3 Schlagworten, z.B. 'Brust, Schultern' oder 'Ausdauer'.")
    blocks: List[BlockSchema] = Field(..., description="Liste der Blöcke, aus denen das Workout besteht.")