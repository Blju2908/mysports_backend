"""
Phase 3: Exercise Filtering Service

Code-based pre-filtering of exercise library based on:
- Recovery percentages and avoid_muscles from Phase 2
- Available equipment
- Movement pattern preferences
- Difficulty level constraints

Reduces exercise pool from 800+ to 50-200 relevant exercises for Phase 4.
"""

from typing import List, Dict, Any
from .phase_2_workout_focus_service import WorkoutFocus


class ExerciseFilteringService:
    """Service for filtering exercises based on recovery and equipment constraints"""
    
    def __init__(self):
        pass
    
    def filter_exercises(
        self,
        exercise_descriptions: List[Dict[str, Any]],
        workout_focus: WorkoutFocus,
        recovery_percentages: Dict[str, float],
        available_equipment: List[str],
        min_recovery_threshold: float = 70.0,
        max_difficulty_level: str = "advanced"
    ) -> List[Dict[str, Any]]:
        """
        Filter exercises based on recovery, equipment, and focus constraints
        
        Args:
            exercise_descriptions: All available exercise descriptions
            workout_focus: Determined workout focus from Phase 2
            recovery_percentages: Muscle recovery percentages
            available_equipment: User's available equipment
            min_recovery_threshold: Minimum recovery percentage to include exercise
            max_difficulty_level: Maximum difficulty level to include
            
        Returns:
            Filtered list of exercise descriptions
        """
        
        filtered_exercises = []
        
        for exercise in exercise_descriptions:
            # Equipment compatibility check
            if not self._check_equipment_compatibility(exercise, available_equipment):
                continue
            
            # Recovery-based filtering
            if not self._check_recovery_compatibility(exercise, recovery_percentages, min_recovery_threshold):
                continue
            
            # Avoid fatigued muscle groups
            if self._targets_avoided_muscles(exercise, workout_focus.avoid_muscles):
                continue
            
            # Difficulty level check
            if not self._check_difficulty_level(exercise, max_difficulty_level):
                continue
            
            # Movement pattern alignment (optional boost for relevant exercises)
            if self._aligns_with_focus(exercise, workout_focus):
                filtered_exercises.append(exercise)
        
        return filtered_exercises
    
    def _check_equipment_compatibility(self, exercise: Dict[str, Any], available_equipment: List[str]) -> bool:
        """Check if exercise can be performed with available equipment"""
        required_equipment = exercise.get("equipment_list", [])
        
        # If no equipment required, always compatible
        if not required_equipment:
            return True
        
        # Check if all required equipment is available
        return all(equipment in available_equipment for equipment in required_equipment)
    
    def _check_recovery_compatibility(
        self, 
        exercise: Dict[str, Any], 
        recovery_percentages: Dict[str, float],
        min_threshold: float
    ) -> bool:
        """Check if targeted muscle groups are sufficiently recovered"""
        muscle_activations = exercise.get("muscle_activations", [])
        
        if not muscle_activations:
            return True  # No muscle data available, allow by default
        
        # Calculate weighted average recovery for this exercise
        total_activation = 0
        weighted_recovery = 0
        
        for activation in muscle_activations:
            muscle_group = activation.get("muscle_group")
            activation_pct = activation.get("activation_percentage", 0)
            
            if muscle_group in recovery_percentages:
                muscle_recovery = recovery_percentages[muscle_group]
                weighted_recovery += muscle_recovery * activation_pct
                total_activation += activation_pct
        
        if total_activation == 0:
            return True
        
        avg_recovery = weighted_recovery / total_activation
        return avg_recovery >= min_threshold
    
    def _targets_avoided_muscles(self, exercise: Dict[str, Any], avoid_muscles: List[str]) -> bool:
        """Check if exercise significantly targets muscles that should be avoided"""
        muscle_activations = exercise.get("muscle_activations", [])
        
        for activation in muscle_activations:
            muscle_group = activation.get("muscle_group")
            activation_pct = activation.get("activation_percentage", 0)
            
            # Avoid exercises that significantly target avoided muscles (>30% activation)
            if muscle_group in avoid_muscles and activation_pct > 30:
                return True
        
        return False
    
    def _check_difficulty_level(self, exercise: Dict[str, Any], max_difficulty: str) -> bool:
        """Check if exercise difficulty is within acceptable range"""
        difficulty_order = ["beginner", "intermediate", "advanced", "expert"]
        exercise_difficulty = exercise.get("difficulty_level", "intermediate")
        
        try:
            exercise_level = difficulty_order.index(exercise_difficulty)
            max_level = difficulty_order.index(max_difficulty)
            return exercise_level <= max_level
        except ValueError:
            # Unknown difficulty level, allow by default
            return True
    
    def _aligns_with_focus(self, exercise: Dict[str, Any], workout_focus: WorkoutFocus) -> bool:
        """Check if exercise aligns with the determined workout focus"""
        muscle_activations = exercise.get("muscle_activations", [])
        exercise_muscles = [act.get("muscle_group") for act in muscle_activations]
        
        # Check for overlap with primary or secondary target muscles
        target_muscles = workout_focus.primary_muscles + workout_focus.secondary_muscles
        muscle_overlap = len(set(exercise_muscles) & set(target_muscles))
        
        return muscle_overlap > 0
    
    def get_filtering_summary(
        self, 
        original_count: int, 
        filtered_count: int,
        workout_focus: WorkoutFocus
    ) -> Dict[str, Any]:
        """Generate summary of filtering results"""
        return {
            "original_exercise_count": original_count,
            "filtered_exercise_count": filtered_count,
            "reduction_percentage": round((1 - filtered_count/original_count) * 100, 1) if original_count > 0 else 0,
            "target_muscles": workout_focus.primary_muscles,
            "avoided_muscles": workout_focus.avoid_muscles,
            "filtering_efficiency": f"Reduced from {original_count} to {filtered_count} exercises"
        }


# Factory function
def create_exercise_filtering_service() -> ExerciseFilteringService:
    """Create and return an ExerciseFilteringService instance"""
    return ExerciseFilteringService()