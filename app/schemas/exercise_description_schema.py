from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ExerciseDescriptionRead(BaseModel):
    model_config = {"from_attributes": True}

    name_german: str = Field(description="Deutscher Name als stabiler Primary Key")
    name_english: str
    description_german: str
    difficulty_level: str
    primary_movement_pattern: str
    is_unilateral: bool
    equipment_options: List[str] = []
    target_muscle_groups: List[str] = []
    execution_steps: List[str] = []
    created_at: datetime
    updated_at: datetime


# ==========================================
# MULTI-PHASE EXERCISE DESCRIPTION SCHEMAS
# ==========================================

class Phase1MuscleActivation(BaseModel):
    """Schema for muscle activation data in exercise descriptions"""
    muscle_group: str
    activation_percentage: int

class Phase1ExerciseDescriptionRead(BaseModel):
    """Schema for Exercise Descriptions in Multi-Phase Workout Generation - flexible for JSON data"""
    model_config = {"from_attributes": True}
    
    # Core fields (only name_english is required)
    name_english: str
    name_german: Optional[str] = None
    description_german: Optional[str] = None
    difficulty_level: Optional[str] = None
    is_unilateral: Optional[bool] = None
    
    # Movement pattern (flexible naming)
    primary_movement_pattern: Optional[str] = None
    movement_pattern: Optional[str] = None  # Alternative field name
    
    # Equipment and muscles (flexible)
    equipment_options: List[str] = []
    equipment_list: List[str] = []  # Alternative field name
    target_muscle_groups: List[str] = []
    
    # Exercise details (optional)
    aliases: List[str] = []
    exercise_type: Optional[str] = None
    is_compound: Optional[bool] = None
    volume_unit: Optional[str] = None
    typical_rep_range: Optional[str] = None
    
    # Muscle activation data (optional, detailed)
    muscle_activations: List[Phase1MuscleActivation] = []
    
    # Instructions (optional)
    setup_steps: List[str] = []
    execution_steps: List[str] = []
    common_mistakes: List[str] = []
    
    # Fatigue and recovery data (optional)
    met_value: Optional[float] = None
    muscle_fatigue_factor: Optional[float] = 1.0
    muscle_recovery_hours: Optional[int] = 48
    recovery_complexity: Optional[str] = "medium"
    
    # Timestamps (flexible)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def get_movement_pattern(self) -> str:
        """Get movement pattern from either field name"""
        return self.primary_movement_pattern or self.movement_pattern or "compound"
    
    def get_equipment_list(self) -> List[str]:
        """Get equipment from either field name"""
        return self.equipment_options or self.equipment_list
    
    def get_muscle_groups_from_activations(self) -> List[str]:
        """Extract muscle groups from activation data"""
        if self.muscle_activations:
            return [activation.muscle_group for activation in self.muscle_activations]
        return self.target_muscle_groups
    
    def get_primary_muscle_groups(self, min_activation: int = 50) -> List[str]:
        """Get primary muscle groups based on activation threshold"""
        if self.muscle_activations:
            return [
                activation.muscle_group 
                for activation in self.muscle_activations 
                if activation.activation_percentage >= min_activation
            ]
        return self.target_muscle_groups[:3]  # Return first 3 as primary 