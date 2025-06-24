from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, List, Union
from datetime import datetime
from enum import Enum
from app.models.set_model import SetStatus

# ==========================================
# SIMPLE SCHEMAS - Nutzt SQLModel's automatische Serialisierung
# ==========================================

class WorkoutStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    DONE = "done"

# ==========================================
# INPUT SCHEMAS - Flexible für Frontend (String/Int IDs)
# ==========================================

class SetInput(BaseModel):
    """Schema für Set Input - flexible IDs für Frontend"""
    id: Optional[Union[int, str]] = None  # Frontend kann temp IDs senden
    exercise_id: Optional[Union[int, str]] = None  # Wird zur Laufzeit gesetzt
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: SetStatus = SetStatus.open
    completed_at: Optional[datetime] = None
    
    @field_validator('completed_at')
    @classmethod
    def make_datetime_naive(cls, v: Optional[datetime]) -> Optional[datetime]:
        """✅ Automatisch timezone-aware datetimes zu naive konvertieren"""
        if v is not None and v.tzinfo is not None:
            return v.replace(tzinfo=None)
        return v

class ExerciseInput(BaseModel):
    """Schema für Exercise Input - flexible IDs für Frontend"""
    id: Optional[Union[int, str]] = None  # Frontend kann temp IDs senden
    block_id: Optional[Union[int, str]] = None  # Wird zur Laufzeit gesetzt
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    sets: List[SetInput] = []

class BlockInput(BaseModel):
    """Schema für Block Input - flexible IDs für Frontend"""
    id: Optional[Union[int, str]] = None  # Frontend kann temp IDs senden
    workout_id: Optional[Union[int, str]] = None  # Wird zur Laufzeit gesetzt
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    exercises: List[ExerciseInput] = []

# ==========================================
# OUTPUT SCHEMAS - Strikte Integer IDs für Response
# ==========================================

# Set Schema - einfach und direkt
class SetRead(BaseModel):
    id: int
    exercise_id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: SetStatus = SetStatus.open
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

# Exercise Schema - ohne komplexe Unions
class ExerciseRead(BaseModel):
    id: int
    block_id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    sets: List[SetRead] = []
    
    class Config:
        from_attributes = True

# Block Schema - sauber und einfach
class BlockRead(BaseModel):
    id: int
    workout_id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    exercises: List[ExerciseRead] = []
    
    class Config:
        from_attributes = True

# Workout Schema - mit computed status
class WorkoutRead(BaseModel):
    id: int
    training_plan_id: Optional[int] = None
    name: str
    date_created: datetime
    description: Optional[str] = None
    duration: Optional[int] = None
    focus: Optional[str] = None
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True
    
    @computed_field
    @property
    def status(self) -> WorkoutStatusEnum:
        """Berechnet Status automatisch - keine separate DB Query nötig!"""
        if not hasattr(self, 'blocks') or not self.blocks:
            return WorkoutStatusEnum.NOT_STARTED
        
        all_sets = [s for block in self.blocks for ex in block.exercises for s in ex.sets]
        if not all_sets:
            return WorkoutStatusEnum.NOT_STARTED
        
        done_sets = [s for s in all_sets if s.status == SetStatus.done]
        
        if len(done_sets) == len(all_sets):
            return WorkoutStatusEnum.DONE
        elif len(done_sets) > 0:
            return WorkoutStatusEnum.STARTED
        return WorkoutStatusEnum.NOT_STARTED

# Detailed Workout - erweitert WorkoutRead
class WorkoutWithBlocksRead(WorkoutRead):
    blocks: List[BlockRead] = []

# ==========================================
# UPDATE SCHEMAS - Nur wenn nötig
# ==========================================

class SetUpdate(BaseModel):
    status: SetStatus
    completed_at: Optional[datetime] = None
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None










