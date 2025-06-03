from pydantic import BaseModel
from typing import List, Optional, Union
from datetime import datetime
from enum import Enum
from app.models.set_model import SetStatus

# Enum for Workout Status
class WorkoutStatusEnum(str, Enum):
    NOT_STARTED = "not_started"
    STARTED = "started"
    DONE = "done"

# Forward declaration for SetResponseSchema if it's used before definition
class SetResponseSchema(BaseModel):
    id: int
    exercise_id: int
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: str # Assuming SetStatus is a string e.g., "open", "done"
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class ExerciseResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    block_id: int
    sets: List[SetResponseSchema]

    class Config:
        from_attributes = True


class BlockResponseSchema(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    workout_id: int
    exercises: List[ExerciseResponseSchema]

    class Config:
        from_attributes = True


class WorkoutSchemaBase(BaseModel):
    name: str
    description: Optional[str] = None
    duration: Optional[int] = None
    focus: Optional[str] = None
    notes: Optional[str] = None

class WorkoutCreateSchema(WorkoutSchemaBase):
    training_plan_id: Optional[int] = None # Can be set explicitly or derived

class WorkoutResponseSchema(WorkoutSchemaBase):
    id: int
    training_plan_id: Optional[int]
    date_created: datetime
    status: WorkoutStatusEnum # Added status field

    class Config:
        from_attributes = True

class WorkoutSchemaWithBlocks(WorkoutResponseSchema): # Inherits from WorkoutResponseSchema
    blocks: List[BlockResponseSchema]

    class Config:
        from_attributes = True

# --- Schemas for Extended Block Activity ---
class NewSetInputSchema(BaseModel):
    local_id: str # Frontend generated temporary ID
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: str # from SetStatus enum
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class NewExerciseInputSchema(BaseModel):
    local_id: str # Frontend generated temporary ID
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    sets: List[NewSetInputSchema]

class SetUpdateInputSchema(BaseModel): # No longer inherits from NewSetInputSchema
    set_id: int # Database ID of the set to update
    # Explicitly define fields needed for update, mirroring NewSetInputSchema minus local_id
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: str # from SetStatus enum
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

class AddedSetsToExistingExerciseSchema(BaseModel):
    existing_exercise_id: int
    new_sets: List[NewSetInputSchema]

class ExtendedBlockActivityPayloadSchema(BaseModel):
    added_exercises: List[NewExerciseInputSchema] = []
    deleted_exercise_ids: List[int] = []
    added_sets_to_existing_exercises: List[AddedSetsToExistingExerciseSchema] = []
    deleted_set_ids: List[int] = []
    updated_sets: List[SetUpdateInputSchema] = []

class IdMappingSchema(BaseModel):
    local_id: str
    db_id: int
    entity_type: str # "exercise" or "set"

class SetSchema(BaseModel):
    id: Optional[Union[int, str]] = None
    exercise_id: Optional[Union[int, str]] = None
    reps: Optional[int] = None
    weight: Optional[float] = None
    duration: Optional[int] = None
    distance: Optional[float] = None
    rest_time: Optional[int] = None
    status: SetStatus
    completed_at: Optional[datetime] = None

class ExerciseSchema(BaseModel):
    id: Optional[Union[int, str]]
    block_id: Optional[Union[int, str]] = None
    name: str
    description: Optional[str]
    notes: Optional[str]
    superset_id: Optional[str] = None
    sets: List[SetSchema]

class BlockSchema(BaseModel):
    id: Optional[Union[int, str]]
    workout_id: Optional[Union[int, str]] = None
    name: str
    description: Optional[str]
    notes: Optional[str]
    exercises: List[ExerciseSchema] 