from typing import Optional, List, TYPE_CHECKING, Dict, Any
from sqlmodel import SQLModel, Field, Relationship
from uuid import UUID
from datetime import date
from sqlalchemy import ARRAY, String, Column, JSON

if TYPE_CHECKING:
    from .user_model import UserModel
    from .workout_model import Workout


class TrainingPlan(SQLModel, table=True):
    __tablename__ = "training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Persönliche Informationen
    gender: Optional[str] = Field(default=None)
    birthdate: Optional[date] = Field(default=None)
    height: Optional[float] = Field(default=None)
    weight: Optional[float] = Field(default=None)
    
    # Trainingsziele - Anpassung, um Frontend-Format direkt zu unterstützen
    goal_details: Optional[str] = Field(default=None)
    workout_styles: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    
    # Erfahrungslevel
    fitness_level: Optional[int] = Field(default=None)
    experience_level: Optional[int] = Field(default=None)
    
    # Trainingsplan
    training_frequency: Optional[int] = Field(default=None)
    session_duration: Optional[int] = Field(default=None)
    other_regular_activities: Optional[str] = Field(default=None)
    
    # Equipment und Umgebung - Anpassung, um Frontend-Format direkt zu unterstützen
    equipment: Optional[List[str]] = Field(
        sa_column=Column(ARRAY(String)), default=None
    )
    equipment_details: Optional[str] = Field(default=None)
    
    # Einschränkungen
    restrictions: Optional[str] = Field(default=None)
    mobility_restrictions: Optional[str] = Field(default=None)
    
    # Comments
    comments: Optional[str] = Field(default=None)

    # Direkte Beziehung zum User (One-to-One)
    user: Optional["UserModel"] = Relationship(back_populates="training_plan")
    
    # Beziehung zu Workouts
    workouts: List["Workout"] = Relationship(back_populates="plan")
