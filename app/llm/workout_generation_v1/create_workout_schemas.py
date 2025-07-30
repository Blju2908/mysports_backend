from pydantic import BaseModel, Field
from typing import List, Optional

class CompactSetSchema(BaseModel):
    """A highly compact, yet structured representation of a single set."""
    r: Optional[int] = Field(None, description="Reps")
    w: Optional[float] = Field(None, description="Weight (kg)")
    s: Optional[int] = Field(None, description="Duration (seconds)")
    d: Optional[int] = Field(None, description="Distance (meters)")
    p: Optional[int] = Field(None, description="Pause (seconds)")


class CompactExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung, exakt wie in der Bibliothek.")
    # Example for a set: {"r": 8, "w": 80.0, "p": 120}
    sets: List[CompactSetSchema] = Field(
        ...,
        description="Liste der Sätze. Fehlende Werte sind null.",
    )
    superset_group: Optional[str] = Field(
        None, description="Gruppe für Supersets (z.B. 'A', 'B')."
    )


class CompactBlockSchema(BaseModel):
    name: str = Field(..., description="Name des Blocks (z.B. 'Warm-Up', 'Main').")
    duration_min: int = Field(..., description="Geschätzte Dauer des Blocks in Minuten.")
    description: str = Field(..., description="Kurze Beschreibung des Block-Fokus.")
    exercises: List[CompactExerciseSchema] = Field(
        ..., description="Liste der Übungen in diesem Block."
    )


class CompactWorkoutSchema(BaseModel):
    muscle_group_load: List[str] = Field(
        ..., description="Analyse der Muskelgruppenbelastung basierend auf der Historie des Users."
    )
    focus_derivation: str = Field(
        ..., description="Herleitung des Workout-Fokus basierend auf der Analyse."
    )
    name: str = Field(..., description="Name des gesamten Workouts.")
    duration_min: int = Field(..., description="Geschätzte Gesamtdauer in Minuten.")
    focus: str = Field(..., description="Hauptfokus des Workouts (z.B. 'Kraft, Muskelaufbau').")
    description: str = Field(
        ..., description="Detailliertere Beschreibung des Workout-Ziels."
    )
    blocks: List[CompactBlockSchema] = Field(
        ..., description="Die Blöcke des Workouts."
    )