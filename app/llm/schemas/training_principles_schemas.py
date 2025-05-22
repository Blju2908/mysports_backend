from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import date

class WorkoutTypeSchema(BaseModel):
    """Workout type with intensity information"""
    type: str = Field(..., description="Type of workout")
    intensity: str = Field(..., description="Intensity level")

class PersonOverviewSchema(BaseModel):
    """Basic information about the person"""
    base_data: str = Field(..., description="Age, gender, height, weight in a concise format")
    training_goals: str = Field(..., description="Brief summary of training goals")
    experience_level: str = Field(..., description="Training experience level and relevant details")
    training_environment: str = Field(..., description="Available equipment and training location")
    limitations: Optional[str] = Field(None, description="Relevant health factors or limitations")

class TrainingPrincipleSchema(BaseModel):
    """Individual training principle with brief explanation"""
    name: str = Field(..., description="Name of the principle")
    explanation: str = Field(..., description="Brief explanation in one sentence")

class TrainingPhaseSchema(BaseModel):
    """Training phase with description and workout recommendations"""
    name: str = Field(..., description="Name of the phase (e.g., 'Base', 'Build', 'Peak')")
    duration: str = Field(..., description="Duration of this phase (e.g., '4-6 weeks'). Include an start and end date. for each phase")
    focus: str = Field(..., description="Main focus of this phase")
    description: str = Field(..., description="Brief description of what happens in this phase")
    workout_types: List[WorkoutTypeSchema] = Field(..., description="List of workout types with their intensity level")

class TrainingPrinciplesSchema(BaseModel):
    """Complete training principles output schema"""
    person_overview: PersonOverviewSchema = Field(..., description="Overview of the person")
    core_principles: List[TrainingPrincipleSchema] = Field(..., description="3-5 key training principles")
    training_recommendation: str = Field(..., description="Concise summary of the most important points for workout creation")
    training_phases: List[TrainingPhaseSchema] = Field(..., description="Training phases with recommendations")
    valid_until: date = Field(..., description="Date until which this training plan is valid") 