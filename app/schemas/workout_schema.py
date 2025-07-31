from pydantic import BaseModel, Field, computed_field, field_validator
from typing import Optional, List, Union, Any, Dict
from datetime import datetime
from enum import Enum
from app.models.set_model import SetStatus, SetTag

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
    position: Optional[int] = Field(default=None, description="Position for stable sorting - auto-assigned if None")
    status: SetStatus = SetStatus.open
    completed_at: Optional[datetime] = None
    tag: Optional[SetTag] = None
    
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
    position: Optional[int] = Field(default=None, description="Position for stable sorting - auto-assigned if None")
    sets: List[SetInput] = []

class BlockInput(BaseModel):
    """Schema für Block Input - flexible IDs für Frontend"""
    id: Optional[Union[int, str]] = None  # Frontend kann temp IDs senden
    workout_id: Optional[Union[int, str]] = None  # Wird zur Laufzeit gesetzt
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    position: Optional[int] = Field(default=None, description="Position for stable sorting - auto-assigned if None")
    exercises: List[ExerciseInput] = []

# ==========================================
# OUTPUT SCHEMAS - Strikte Integer IDs für Response
# ==========================================

# Set Schema - einfach und direkt
class SetRead(BaseModel):
    model_config = {"from_attributes": True}  # ✅ SQLModel Best Practice!
    
    id: int
    exercise_id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    position: Optional[int] = None
    status: SetStatus = SetStatus.open
    completed_at: Optional[datetime] = None
    tag: Optional[SetTag] = None

# Exercise Schema - ohne komplexe Unions
class ExerciseRead(BaseModel):
    model_config = {"from_attributes": True}  # ✅ SQLModel Best Practice!
    
    id: int
    block_id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    position: Optional[int] = None
    sets: List[SetRead] = []

# Block Schema - sauber und einfach
class BlockRead(BaseModel):
    model_config = {"from_attributes": True}  # ✅ SQLModel Best Practice!
    
    id: int
    workout_id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    position: Optional[int] = None
    exercises: List[ExerciseRead] = []

# ==========================================
# WORKOUT SCHEMAS - Optimiert für verschiedene Use Cases
# ==========================================

# Schlankes Schema für Workout-Listen (ohne Relations)
class WorkoutListRead(BaseModel):
    """Effizientes Schema für Workout-Listen ohne Relations - minimaler Traffic"""
    model_config = {"from_attributes": True}
    
    id: int
    training_plan_id: Optional[int] = None
    name: str
    date_created: datetime
    description: Optional[str] = None
    duration: Optional[int] = None
    focus: Optional[str] = None
    notes: Optional[str] = None
    status: WorkoutStatusEnum  # ✅ Wird direkt von der DB gesetzt

# Vollständiges Schema für Workout-Details (mit Relations)
class WorkoutRead(BaseModel):
    """Vollständiges Schema mit Relations für Detail-Ansichten"""
    model_config = {"from_attributes": True}  # ✅ SQLModel Best Practice!
    
    id: int
    training_plan_id: Optional[int] = None
    name: str
    date_created: datetime
    description: Optional[str] = None
    duration: Optional[int] = None
    focus: Optional[str] = None
    notes: Optional[str] = None
    muscle_group_load: Optional[List[str]] = None
    focus_derivation: Optional[str] = None
    blocks: List[BlockRead] = []
    
    @computed_field
    @property
    def status(self) -> WorkoutStatusEnum:
        """Berechnet Status aus geladenen Relations"""
        if not self.blocks:
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

# Detailed Workout - erweitert WorkoutRead (für Backward Compatibility)
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
    tag: Optional[SetTag] = None


# ==========================================
# MULTI-PHASE WORKOUT GENERATION SCHEMAS
# ==========================================

class Phase1SetRead(BaseModel):
    """Schema for Sets in Multi-Phase Workout Generation - optimized for local JSON data"""
    model_config = {"from_attributes": True}
    
    id: int
    exercise_id: Optional[int] = None  # Will be set programmatically
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    rest_time: Optional[int] = None  # in seconds
    position: Optional[int] = None
    status: str = "open"  # Using string for JSON compatibility
    completed_at: Optional[datetime] = None
    tag: Optional[str] = None  # Using string for JSON compatibility

class Phase1ExerciseRead(BaseModel):
    """Schema for Exercises in Multi-Phase Workout Generation - flattened for muscle fatigue analysis"""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    position: Optional[int] = None
    
    # Context information from parent structures
    block_id: int
    workout_id: int
    workout_name: str
    workout_date: str
    workout_focus: Optional[str] = None
    
    # Sets data
    sets: List[Phase1SetRead] = []
    
    # Optional: Exercise description will be added later
    exercise_description: Optional[Any] = None

class Phase1BlockRead(BaseModel):
    """Schema for Blocks in Multi-Phase Workout Generation"""
    model_config = {"from_attributes": True}
    
    id: int
    name: str
    description: Optional[str] = None
    position: Optional[int] = None
    exercises: List[Phase1ExerciseRead] = []  # Raw exercise data from JSON

class Phase1WorkoutRead(BaseModel):
    """Schema for complete Workouts in Multi-Phase Workout Generation"""
    model_config = {"from_attributes": True}
    
    id: int
    user_id: str  # UUID as string from JSON
    name: str
    date_created: str  # ISO string from JSON
    description: Optional[str] = None
    duration: Optional[int] = None
    focus: Optional[str] = None
    notes: Optional[str] = None
    blocks: List[Phase1BlockRead] = []










