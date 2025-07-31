from pydantic import BaseModel, Field
from typing import List, Optional, Union

class ArrayExerciseSchema(BaseModel):
    """Array-based exercise representation for maximum compression."""
    name: str = Field(..., description="Name der Übung, exakt wie in der Bibliothek.")
    
    # Arrays where position = set number (0-indexed)
    reps: Optional[List[int]] = Field(None, description="Wiederholungen pro Satz")
    weight: Optional[Union[float, List[float]]] = Field(None, description="Gewicht in kg (einzelner Wert oder Array)")
    duration: Optional[List[int]] = Field(None, description="Dauer in Sekunden pro Satz")
    distance: Optional[List[int]] = Field(None, description="Distanz in Metern pro Satz")
    rest: Optional[Union[int, List[int]]] = Field(None, description="Pause in Sekunden (einzelner Wert oder Array)")
    tags: Optional[List[str]] = Field(None, description="Tags pro Satz (z.B. 'warm_up')")
    
    # Optional fields
    superset: Optional[str] = Field(None, description="Superset-Gruppe (z.B. 'A', 'B')")
    note: Optional[str] = Field(None, description="Zusätzliche Hinweise (z.B. 'drop', 'rest-pause')")
    equipment_note: Optional[str] = Field(None, description="Equipment-spezifische Hinweise")

class CompactBlockSchema(BaseModel):
    name: str = Field(..., description="Name des Blocks (z.B. 'Warm-Up', 'Main').")
    duration_min: int = Field(..., description="Geschätzte Dauer des Blocks in Minuten.")
    exercises: List[ArrayExerciseSchema] = Field(
        ..., description="Liste der Übungen in diesem Block."
    )

class CompactWorkoutSchema(BaseModel):
    focus_derivation: str = Field(
        ..., description="1-2 Sätze zur Begründung des Workout-Fokus."
    )
    name: str = Field(..., description="Name des gesamten Workouts.")
    duration_min: int = Field(..., description="Geschätzte Gesamtdauer in Minuten.")
    focus: str = Field(..., description="Hauptfokus des Workouts (z.B. 'Kraft, Muskelaufbau').")
    description: str = Field(
        ..., description="Kurze Beschreibung des Workouts."
    )
    blocks: List[CompactBlockSchema] = Field(
        ..., description="Die Blöcke des Workouts."
    )