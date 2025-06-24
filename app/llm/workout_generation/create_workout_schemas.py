from pydantic import BaseModel, Field
from typing import List, Optional, Union

class SetSchema(BaseModel):
    values: List[Optional[Union[float, int, str]]] = Field(
        default_factory=list, 
        description="Geplante Werte in der Reihenfolge: [Gewicht (immer in kg nicht 1RM oder BW, PFLICHT bei Kraftübungen), Wdh, Dauer (sekunden), Distanz (m/km), Pause (sekunden)]. Für Zahlenwerte Null oder den Wert eintragen."
    )

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung.")
    sets: List[SetSchema] = Field(..., description="Liste der Sätze für diese Übung.")
    superset_id: Optional[str] = Field(default=None, description="Eindeutige ID für Supersets. Übungen mit derselben superset_id werden abwechselnd ausgeführt (z.B. 'A', 'B', 'C'). Null für normale Übungen ohne Superset.")

class BlockSchema(BaseModel):
    name: str = Field(..., description="Name des Workout-Blocks (z.B. Aufwärmen, Hauptteil, Cooldown).")
    description: str = Field(..., description="Beschreibung des Blocks.")
    exercises: List[ExerciseSchema] = Field(..., description="Liste der Übungen in diesem Block.")

class WorkoutSchema(BaseModel):
    name: str = Field(..., description="Name des Workouts. z.B. 'Push-Training'")
    description: str = Field(..., description="Kurze Beschreibung des gesamten Workouts.")
    duration: int = Field(..., description="Dauer des Workouts in Minuten.")
    focus: str = Field(..., description="Hauptfokus des Workouts in max. 3 Schlagworten, z.B. 'Brust, Schultern' oder 'Ausdauer'.")
    blocks: List[BlockSchema] = Field(..., description="Liste der Blöcke, aus denen das Workout besteht.")