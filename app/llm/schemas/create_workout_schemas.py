from pydantic import BaseModel, Field
from typing import List, Optional, Union

class SetSchema(BaseModel):
    values: List[Optional[Union[float, int]]] = Field(
        default_factory=lambda: [None] * 6, # Default to a list of 6 Nones
        description="Geplante Werte in der Reihenfolge: [Gewicht (kg), Wdh, Dauer (sekunden), Distanz (m/km), Pause (sekunden)]. Null eintragen, wenn nicht relevant."
    )
    notes: Optional[str] = Field(default=None, description="Optionale Notizen für diesen spezifischen Satz z.B. 'langsame Ausführung', 'bis Muskelversagen'")

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung.")
    description: Optional[str] = Field(default=None, description="Kurze Beschreibung der Übung, z.B. Ausführungshinweise, Zielfokus")
    sets: List[SetSchema] = Field(..., description="Liste der Sätze für diese Übung.")

class BlockSchema(BaseModel):
    name: str = Field(..., description="Name des Workout-Blocks (z.B. Aufwärmen, Hauptteil, Cooldown).")
    description: Optional[str] = Field(default=None, description="Optionale Beschreibung des Blocks.")
    exercises: List[ExerciseSchema] = Field(..., description="Liste der Übungen in diesem Block.")

class WorkoutSchema(BaseModel):
    name: str = Field(..., description="Name des Workouts. z.B. 'Push-Training'")
    description: str = Field(default=None, description="Kurze Beschreibung des gesamten Workouts.")
    duration: int = Field(default=None, description="Dauer des Workouts in Minuten.")
    focus: str = Field(default=None, description="Hauptfokus des Workouts, z.B. 'Brust, Schultern' oder 'Ausdauer'.")
    blocks: List[BlockSchema] = Field(..., description="Liste der Blöcke, aus denen das Workout besteht.")