from typing import Optional, List, TYPE_CHECKING, Dict, Any, Union
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
from datetime import date
from sqlalchemy import ARRAY, String, Column, JSON
from pydantic import field_validator

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workout_model import Workout

class TrainingProfile(SQLModel, table=True):
    __tablename__ = "training_profiles"
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id") # Link to user
    name: Optional[str] = Field(default=None) # New: Name of the profile
    equipment: Optional[str] = Field(default=None)
    equipment_llm_context: Optional[str] = Field(default=None) # New: LLM context for equipment
    equipment_details: Optional[str] = Field(default=None)
    is_primary: Optional[bool] = Field(default=False)

class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Foreign Key zum User (One-to-One Beziehung)
    user_id: UUID = Field(foreign_key="users.id", unique=True)
    
    # Persönliche Informationen
    gender: Optional[str] = Field(default=None)
    birthdate: Optional[date] = Field(default=None) # TODO: Remove after version migration
    age: Optional[int] = Field(default=None)
    height: Optional[float] = Field(default=None)
    weight: Optional[float] = Field(default=None)
    
    # Trainingsziele - Anpassung, um Frontend-Format direkt zu unterstützen
    workout_goal_id: Optional[str] = Field(default=None)
    workout_goal_llm_context: Optional[str] = Field(default=None)
    goal_details: Optional[str] = Field(default=None)
    workout_styles: Optional[List[str]] = Field(  
        sa_column=Column(ARRAY(String)), default=None
    ) # TODO: Remove after version migration
    
    # Fitnesslevel
    fitness_level: Optional[int] = Field(default=None)
    fitness_level_description: Optional[str] = Field(default=None)

    # Erfahrungslevel
    experience_level: Optional[int] = Field(default=None)
    experience_level_description: Optional[str] = Field(default=None)
    
    # Trainingsplan
    training_frequency: Optional[int] = Field(default=None)
    session_duration: Optional[int] = Field(default=None)
    other_regular_activities: Optional[str] = Field(default=None)
    
    # Equipment und Umgebung - Diese bleiben für Abwärtskompatibilität bestehen.
    equipment: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    equipment_details: Optional[str] = Field(default=None)

    @field_validator('equipment', mode='before')
    def validate_equipment_field(cls, v: Union[str, List[str], None]) -> Optional[str]:
        if isinstance(v, list):
            # If it's a list, take the first element if available, otherwise None.
            # This ensures compatibility with the string field in the DB for legacy clients.
            # The actual equipment data is derived from training_profiles.
            return v[0] if v else None
        return v

    # Einschränkungen
    restrictions: Optional[str] = Field(default=None)
    mobility_restrictions: Optional[str] = Field(default=None)
    
    # Comments
    comments: Optional[str] = Field(default=None)

    # One-to-One Beziehung zum User
    user: "UserModel" = Relationship(back_populates="training_plan")
    
    # Beziehung zu Workouts (für Kontext - primäre Beziehung ist jetzt User->Workout)
    workouts: List["Workout"] = Relationship(back_populates="plan")
