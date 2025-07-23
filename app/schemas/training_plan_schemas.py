from typing import Optional, List
from pydantic import BaseModel
from datetime import date
from uuid import UUID

# Schemas for TrainingProfile
class TrainingProfileCreate(BaseModel):
    name: Optional[str] = None # New: Name of the profile
    equipment: Optional[str] = None
    equipment_llm_context: Optional[str] = None # New: LLM context for equipment
    equipment_details: Optional[str] = None
    is_primary: Optional[bool] = False

class TrainingProfileRead(TrainingProfileCreate):
    id: Optional[int] = None

# Schemas for TrainingPlan
class TrainingPlanCreate(BaseModel):
    gender: Optional[str] = None
    birthdate: Optional[date] = None # Will be removed in later migration
    age: Optional[int] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    workout_goal_id: Optional[str] = None
    workout_goal_llm_context: Optional[str] = None
    goal_details: Optional[str] = None
    training_frequency: Optional[int] = None
    session_duration: Optional[int] = None
    other_regular_activities: Optional[str] = None
    equipment: Optional[List[str]] = None # Will be removed in later migration
    equipment_details: Optional[str] = None
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    comments: Optional[str] = None
    fitness_level: Optional[int] = None
    fitness_level_description: Optional[str] = None
    experience_level: Optional[int] = None
    experience_level_description: Optional[str] = None

class TrainingPlanRead(TrainingPlanCreate):
    id: Optional[int] = None
    user_id: Optional[UUID] = None


