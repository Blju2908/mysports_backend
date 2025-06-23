from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.set_model import SetStatus # For SetResponseSchema
# No BlockStatus as it was removed from block_model

# ✅ ADD: Import WorkoutStatusEnum for enhanced list API
from app.llm.schemas.workout_schema import WorkoutStatusEnum

# Base Schemas for individual models - ensuring consistency with DB models

class SetBaseSchema(BaseModel):
    weight: Optional[float] = None
    reps: Optional[int] = None
    duration: Optional[int] = None  # in seconds
    distance: Optional[float] = None
    
    # Common values
    rest_time: Optional[int] = None  # in seconds
    
    # Status tracking
    status: SetStatus = Field(default=SetStatus.open)
    completed_at: Optional[datetime] = None

class SetResponseSchema(SetBaseSchema):
    id: int
    exercise_id: int
    
    class Config:
        from_attributes = True

class ExerciseBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    superset_id: Optional[str] = None
    is_amrap: bool = Field(default=False)

class ExerciseResponseSchema(ExerciseBaseSchema):
    id: int
    block_id: int
    sets: List[SetResponseSchema] = []
    
    class Config:
        from_attributes = True

class BlockBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    notes: Optional[str] = None
    is_amrap: bool = Field(default=False)
    amrap_duration_minutes: Optional[int] = None

class BlockResponseSchema(BlockBaseSchema):
    id: int
    workout_id: int
    exercises: List[ExerciseResponseSchema] = []
    
    class Config:
        from_attributes = True

class WorkoutBaseSchema(BaseModel):
    name: str
    description: Optional[str] = None
    duration: Optional[int] = None 
    focus: Optional[str] = None 
    notes: Optional[str] = None

class WorkoutResponseSchema(WorkoutBaseSchema):
    id: int
    training_plan_id: Optional[int] = None # from workout_model
    date_created: datetime # from workout_model
    # ✅ ADD: Status field for optimized list API - no more frontend status calculation needed!
    status: WorkoutStatusEnum
    
    class Config:
        from_attributes = True

# Schema for workout details including blocks, exercises, and sets
class WorkoutSchemaWithBlocks(WorkoutResponseSchema): # Inherits from WorkoutResponseSchema (now including status!)
    blocks: List[BlockResponseSchema] = []
    
    class Config:
        from_attributes = True

# --- Schemas for Extended Block Activity Saving ---

class NewSetInputSchema(SetBaseSchema): # Inherits planned values, status, etc.
    local_id: str # Frontend temporary ID
    # exercise_id will be determined by the context (new exercise or existing exercise)

class NewExerciseInputSchema(ExerciseBaseSchema): # Inherits name, description, notes, is_amrap
    local_id: str # Frontend temporary ID
    sets: List[NewSetInputSchema] = Field(default_factory=list)
    # block_id will be taken from the endpoint's path parameter

class AddedSetsToExistingExerciseInputSchema(BaseModel):
    existing_exercise_id: int
    new_sets: List[NewSetInputSchema] = Field(default_factory=list)

class SetUpdateInputSchema(SetBaseSchema): # For updating existing sets
    set_id: int # Backend ID of the set to update
    # Inherits status, completed_at, weight, reps, duration, distance, notes from SetBaseSchema
    # It's crucial this matches the structure used in the frontend's UserWorkoutSetExecutionData, adapted for Pydantic
    # Specifically, ensure fields like execution_weight map to weight, etc. if needed.
    # For now, assuming direct mapping from SetBaseSchema is sufficient.

class ExtendedBlockActivityPayloadSchema(BaseModel):
    # workout_id and block_id will come from path parameters, not in payload body
    # to align with how save_block_activity_endpoint currently gets them.
    # If you prefer them in payload, we can add:
    # workout_id: int
    # block_id: int
    
    added_exercises: List[NewExerciseInputSchema] = Field(default_factory=list)
    deleted_exercise_ids: List[int] = Field(default_factory=list) # Backend IDs of exercises to delete
    
    added_sets_to_existing_exercises: List[AddedSetsToExistingExerciseInputSchema] = Field(default_factory=list)
    deleted_set_ids: List[int] = Field(default_factory=list) # Backend IDs of sets to delete
    
    updated_sets: List[SetUpdateInputSchema] = Field(default_factory=list) # For existing sets that are modified

class IdMappingSchema(BaseModel):
    local_id: str
    db_id: int
    entity_type: str # "exercise" or "set"

class SaveBlockResponseSchema(BaseModel):
    message: str
    id_mappings: List[IdMappingSchema] = Field(default_factory=list)
