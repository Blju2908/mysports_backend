from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Union

class SetSchema(BaseModel):
    values: List[Optional[Union[float, int]]] = Field(
        description="EXAKT 5 Werte in fester Reihenfolge: [Gewicht_kg, Wiederholungen, Dauer_sek, Distanz_m, Pause_sek]. Für nicht relevante Werte null verwenden, für relevante Werte IMMER konkrete Zahlen eintragen."
    )
    position: int = Field(default=0, description="Position des Sets in der Exercise.")
    
    @field_validator('values')
    @classmethod
    def validate_values_length(cls, v):
        if len(v) != 5:
            raise ValueError('values array must contain exactly 5 elements: [Gewicht_kg, Wiederholungen, Dauer_sek, Distanz_m, Pause_sek]')
        return v

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