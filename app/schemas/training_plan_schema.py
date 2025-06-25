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
    id: Optional[int] = None
    
    # Personal Info
    gender: Optional[str] = None
    birthdate: Optional[date] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    
    # Training Goals
    goal_details: Optional[str] = None
    workout_styles: Optional[List[str]] = Field(default_factory=list)
    
    # Experience & Fitness
    fitness_level: Optional[int] = None
    experience_level: Optional[int] = None
    
    # Training Schedule
    training_frequency: Optional[int] = None
    session_duration: Optional[int] = None
    other_regular_activities: Optional[str] = None
    
    # Equipment & Environment
    equipment: Optional[List[str]] = Field(default_factory=list)
    equipment_details: Optional[str] = None
    
    # Restrictions & Limitations
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    
    # Comments
    comments: Optional[str] = None
    
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