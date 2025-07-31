"""
Minimale Workout Schemas für Performance-optimierte Generation.
"""

from pydantic import BaseModel, Field
from typing import List

# Minimale Schemas für schnellere Generation
class MinimalExerciseSchema(BaseModel):
    """Minimale Übungsdarstellung - nur Name und Anzahl Sets."""
    name: str = Field(..., description="Name der Übung")
    sets: int = Field(..., description="Anzahl der Sets")


class MinimalBlockSchema(BaseModel):
    """Minimaler Block - nur Name und Übungen."""
    name: str = Field(..., description="Block Name")
    exercises: List[MinimalExerciseSchema] = Field(..., description="Übungen")


class MinimalWorkoutSchema(BaseModel):
    """Minimales Workout Schema für Performance-Tests."""
    name: str = Field(..., description="Name des Workouts")
    focus: str = Field(..., description="Kurzer Fokus (max 10 Wörter)")
    blocks: List[MinimalBlockSchema] = Field(..., description="Workout Blöcke")