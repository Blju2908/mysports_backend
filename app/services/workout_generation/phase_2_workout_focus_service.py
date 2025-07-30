"""
Phase 2: Workout Focus Determination Service

LLM-assisted intelligent decision making for training focus based on:
- Muscle recovery percentages from Phase 1
- Training goals and preferences  
- User prompt and context
- Calendar context (days since last workout)

This service determines which muscle groups to target, avoid, and the overall workout focus.
"""

from typing import Dict, List, Any
from dataclasses import dataclass


@dataclass
class WorkoutFocus:
    """Data class representing determined workout focus"""
    primary_muscles: List[str]
    secondary_muscles: List[str]
    avoid_muscles: List[str]
    workout_type: str  # strength, cardio, flexibility, hybrid
    intensity: str  # low, moderate, high
    movement_focus: str  # push_dominant, pull_dominant, legs_dominant, full_body
    rationale: str


class WorkoutFocusService:
    """Service for determining optimal workout focus using LLM assistance"""
    
    def __init__(self):
        pass
    
    def determine_workout_focus(
        self,
        recovery_percentages: Dict[str, float],
        user_goals: str = "general_fitness",
        session_duration: int = 60,
        user_prompt: str = "",
        days_since_last_workout: int = 1
    ) -> WorkoutFocus:
        """
        Determine workout focus based on recovery data and user context
        
        Args:
            recovery_percentages: Muscle recovery percentages from Phase 1
            user_goals: Training goals (strength, hypertrophy, endurance, etc.)
            session_duration: Available workout time in minutes
            user_prompt: Specific user requests
            days_since_last_workout: Days since last training session
            
        Returns:
            WorkoutFocus object with determined training focus
        """
        
        # TODO: Implement LLM-based focus determination
        # For now, return a rule-based placeholder
        
        return self._rule_based_focus_determination(
            recovery_percentages, 
            user_goals, 
            session_duration,
            days_since_last_workout
        )
    
    def _rule_based_focus_determination(
        self,
        recovery_percentages: Dict[str, float],
        user_goals: str,
        session_duration: int,
        days_since_last_workout: int
    ) -> WorkoutFocus:
        """Placeholder rule-based focus determination until LLM integration"""
        
        well_recovered = [muscle for muscle, recovery in recovery_percentages.items() if recovery >= 85]
        poorly_recovered = [muscle for muscle, recovery in recovery_percentages.items() if recovery < 70]
        
        # Simple logic for demonstration
        if len(well_recovered) >= 3:
            primary_muscles = well_recovered[:3]
            workout_type = "strength"
            intensity = "moderate"
        else:
            # Light recovery workout
            primary_muscles = [muscle for muscle, recovery in recovery_percentages.items() if recovery >= 75][:2]
            workout_type = "flexibility"
            intensity = "low"
        
        return WorkoutFocus(
            primary_muscles=primary_muscles,
            secondary_muscles=[],
            avoid_muscles=poorly_recovered,
            workout_type=workout_type,
            intensity=intensity,
            movement_focus="balanced",
            rationale=f"Selected {len(primary_muscles)} well-recovered muscle groups. Avoiding {len(poorly_recovered)} fatigued areas."
        )


# Factory function
def create_workout_focus_service() -> WorkoutFocusService:
    """Create and return a WorkoutFocusService instance"""
    return WorkoutFocusService()