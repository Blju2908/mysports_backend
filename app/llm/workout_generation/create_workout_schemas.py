from pydantic import BaseModel, Field
from typing import List, Optional, Union

class SetSchema(BaseModel):
    values: List[Optional[Union[float, int, str]]] = Field(
        default_factory=list, 
        description="Geplante Werte in der Reihenfolge: [Gewicht (immer in kg nicht 1RM oder BW, PFLICHT bei Kraftübungen), Wdh, Dauer (sekunden), Distanz (m/km), Pause (sekunden)]. Für Zahlenwerte Null oder den Wert eintragen. Für Notizen einen String oder Null/leeren String. WICHTIG: Bei allen Kraftübungen mit externen Gewichten (Langhantel, Kurzhantel, Kabelzug) MUSS ein realistisches Gewicht angegeben werden - niemals null oder leer!"
    )

class ExerciseSchema(BaseModel):
    name: str = Field(..., description="Name der Übung.")
    description: Optional[str] = Field(default=None, description="Kurze Beschreibung der Übung, z.B. Ausführungshinweise, Zielfokus")
    sets: List[SetSchema] = Field(..., description="Liste der Sätze für diese Übung.")
    superset_id: Optional[str] = Field(default=None, description="Eindeutige ID für Supersets. Übungen mit derselben superset_id werden abwechselnd ausgeführt (z.B. 'A', 'B', 'C'). Null für normale Übungen ohne Superset. WICHTIG: Bei normalen Gym Sessions sparsam verwenden (max. 1-2 Supersets), bei HIIT/Crossfit häufiger (3-5 Supersets).")
    


class BlockSchema(BaseModel):
    name: str = Field(..., description="Name des Workout-Blocks (z.B. Aufwärmen, Hauptteil, Cooldown).")
    description: Optional[str] = Field(default=None, description="Optionale Beschreibung des Blocks.")
    exercises: List[ExerciseSchema] = Field(..., description="Liste der Übungen in diesem Block.")
    is_amrap: bool = Field(default=False, description="True, wenn der Block ein AMRAP Block ist.")
    amrap_duration_minutes: Optional[int] = Field(default=None, description="Gesamtdauer des AMRAP-Blocks in Minuten. Nur setzen, wenn is_amrap True ist.")

class WorkoutSchema(BaseModel):
    name: str = Field(..., description="Name des Workouts. z.B. 'Push-Training'")
    description: str = Field(default=None, description="Kurze Beschreibung des gesamten Workouts.")
    duration: int = Field(default=None, description="Dauer des Workouts in Minuten.")
    focus: str = Field(default=None, description="Hauptfokus des Workouts in max. 3 Schlagworten, z.B. 'Brust, Schultern' oder 'Ausdauer'.")
    blocks: List[BlockSchema] = Field(..., description="Liste der Blöcke, aus denen das Workout besteht.")