from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union, Tuple

class SetSchema(BaseModel):
    reps: Optional[int] = Field(None, description="Anzahl der Wiederholungen.")
    duration_seconds: Optional[int] = Field(None, description="Dauer der Übung in Sekunden.")
    weight: Optional[float] = Field(None, description="Gewicht in Kilogramm für die Übung.")
    distance: Optional[float] = Field(None, description="Distanz in Metern für die Übung.")
    rest_seconds: Optional[int] = Field(None, description="Pause nach dem Satz in Sekunden.")

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung.")
    sets: List[SetSchema] = Field(..., description="Liste der Sätze für diese Übung.")
    superset_group: Optional[str] = Field(default=None, description="Gruppe für Supersets. Übungen mit derselben superset_group werden abwechselnd ausgeführt (z.B. 'A', 'B', 'C'). Null für normale Übungen ohne Superset.")
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


# ---- New Compact Schemas for direct, information-dense LLM output ----

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
        ..., description="Analyse der Muskelgruppenbelastung."
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