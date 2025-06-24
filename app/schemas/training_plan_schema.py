# backend/app/schemas/training_plan_schema.py - OPTIMIZED VERSION
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Any
from datetime import date

# ==========================================
# ✅ SUPER SIMPLIFIED SCHEMA - Best Practice
# ==========================================

class TrainingPlanSchema(BaseModel):
    """
    ✅ CLEAN SCHEMA: Direkte SQLModel Serialisierung ohne komplexe Konvertierungen
    """
    id: Optional[int]
    
    # Personal Info
    gender: Optional[str]
    birthdate: Optional[date]
    height: Optional[float]
    weight: Optional[float]
    
    # Training Goals
    goal_details: Optional[str]
    workout_styles: Optional[List[str]] = Field(default_factory=list)
    
    # Experience & Fitness
    fitness_level: Optional[int]
    experience_level: Optional[int]
    
    # Training Schedule
    training_frequency: Optional[int]
    session_duration: Optional[int]
    other_regular_activities: Optional[str]
    
    # Equipment & Environment
    equipment: Optional[List[str]] = Field(default_factory=list)
    equipment_details: Optional[str]
    
    # Restrictions & Limitations
    restrictions: Optional[str]
    mobility_restrictions: Optional[str]
    
    # Comments
    comments: Optional[str]
    
    # ✅ MINIMAL VALIDATORS - Nur wo wirklich nötig!
    @field_validator('equipment', 'workout_styles', mode='before')
    @classmethod
    def ensure_list(cls, v):
        """Ensure fields are always lists, never None"""
        if v is None:
            return []
        if isinstance(v, str) and v.strip() == "":
            return []
        if isinstance(v, str):
            return [v.strip()]
        return v
    
    class Config:
        from_attributes = True  # ✅ Für SQLModel Auto-Serialization!

class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: Optional[str] = None