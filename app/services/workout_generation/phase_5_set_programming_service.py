"""
Phase 5: Set Programming Service

Code-based automatic calculation of sets, reps, weight, and rest periods based on:
- Exercise-specific progression algorithms
- User's workout history and performance
- Recovery level and training focus
- Volume unit specific calculations (reps_only, reps_and_weight, time_based)
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta
from app.schemas.workout_schema import ExerciseRead


class SetProgrammingService:
    """Service for calculating optimal sets, reps, weight, and rest periods"""
    
    def __init__(self):
        pass
    
    def program_exercise_sets(
        self,
        exercise_data: Dict[str, Any],
        workout_history: List[ExerciseRead],
        recovery_level: float,
        target_duration: int = 10  # minutes per exercise
    ) -> Dict[str, Any]:
        """
        Calculate optimal set programming for an exercise
        
        Args:
            exercise_data: Exercise description with volume_unit, typical_rep_range, etc.
            workout_history: User's previous performances of this exercise
            recovery_level: Recovery percentage for primary muscles (0-100)
            target_duration: Target time allocation per exercise in minutes
            
        Returns:
            Programming details with sets, reps, weight, rest, etc.
        """
        
        last_performance = self._find_last_performance(exercise_data, workout_history)
        volume_unit = exercise_data.get("volume_unit", "reps_only")
        
        if volume_unit == "reps_only":
            return self._program_bodyweight_sets(exercise_data, last_performance, recovery_level)
        elif volume_unit == "reps_and_weight":
            return self._program_weighted_sets(exercise_data, last_performance, recovery_level)
        elif volume_unit == "time_based":
            return self._program_time_sets(exercise_data, last_performance, recovery_level)
        else:
            # Default fallback
            return self._program_bodyweight_sets(exercise_data, last_performance, recovery_level)
    
    def _find_last_performance(
        self, 
        exercise_data: Dict[str, Any], 
        workout_history: List[ExerciseRead]
    ) -> ExerciseRead | None:
        """Find the most recent performance of this exercise"""
        exercise_name = exercise_data.get("name_german", "")
        
        for exercise in reversed(workout_history):  # Most recent first
            if exercise.name.lower() == exercise_name.lower():
                return exercise
        
        return None
    
    def _program_bodyweight_sets(
        self,
        exercise_data: Dict[str, Any],
        last_performance: ExerciseRead | None,
        recovery_level: float
    ) -> Dict[str, Any]:
        """Program sets for bodyweight/calisthenics exercises (reps_only)"""
        
        typical_rep_range = exercise_data.get("typical_rep_range", "8-12")
        min_reps, max_reps = self._parse_rep_range(typical_rep_range)
        
        if not last_performance or not last_performance.sets:
            # New exercise - conservative starting point
            target_reps = min_reps
            sets = 3
        else:
            # Progression based on last performance
            last_reps = max(set_data.reps or 0 for set_data in last_performance.sets)
            days_since = self._days_since_performance(last_performance)
            
            # Adjust based on recovery and time since last workout
            if recovery_level >= 85 and days_since <= 3:
                # Good recovery, recent training - progress
                target_reps = min(last_reps + 1, max_reps)
                sets = len(last_performance.sets)
            elif recovery_level < 70:
                # Poor recovery - reduce volume
                target_reps = max(last_reps - 2, min_reps)
                sets = max(len(last_performance.sets) - 1, 2)
            elif days_since >= 7:
                # Long break - slight deload
                target_reps = max(last_reps - 1, min_reps)
                sets = len(last_performance.sets)
            else:
                # Maintain current level
                target_reps = last_reps
                sets = len(last_performance.sets)
        
        # Rest time based on exercise complexity
        rest_seconds = self._calculate_rest_time(exercise_data, recovery_level)
        
        return {
            "sets": sets,
            "target_reps": target_reps,
            "rep_range": f"{max(target_reps-2, min_reps)}-{min(target_reps+2, max_reps)}",
            "weight": None,
            "rest_seconds": rest_seconds,
            "progression_notes": f"Bodyweight progression - aim for {target_reps} reps per set",
            "volume_unit": "reps_only"
        }
    
    def _program_weighted_sets(
        self,
        exercise_data: Dict[str, Any],
        last_performance: ExerciseRead | None,
        recovery_level: float
    ) -> Dict[str, Any]:
        """Program sets for weighted exercises (reps_and_weight)"""
        
        typical_rep_range = exercise_data.get("typical_rep_range", "8-12")
        min_reps, max_reps = self._parse_rep_range(typical_rep_range)
        
        if not last_performance or not last_performance.sets:
            # New exercise - conservative starting point
            return {
                "sets": 3,
                "target_reps": (min_reps + max_reps) // 2,
                "rep_range": typical_rep_range,
                "weight": "Start with light weight - focus on form",
                "rest_seconds": self._calculate_rest_time(exercise_data, recovery_level),
                "progression_notes": "New exercise - establish baseline weight",
                "volume_unit": "reps_and_weight"
            }
        
        # Calculate progression based on last performance
        last_weight = max(set_data.weight or 0 for set_data in last_performance.sets)
        last_reps = max(set_data.reps or 0 for set_data in last_performance.sets)
        days_since = self._days_since_performance(last_performance)
        
        # Load adjustment based on recovery and time
        if recovery_level >= 85 and days_since <= 3 and last_reps >= max_reps:
            # Good recovery, recent training, hitting high reps - increase weight
            new_weight = last_weight * 1.05
            target_reps = min_reps
            progression_notes = "Increased weight - reset to lower rep range"
        elif recovery_level < 70:
            # Poor recovery - reduce load
            new_weight = last_weight * 0.95
            target_reps = last_reps
            progression_notes = "Reduced weight due to incomplete recovery"
        elif days_since >= 7:
            # Long break - slight deload
            new_weight = last_weight * 0.92
            target_reps = (min_reps + max_reps) // 2
            progression_notes = "Deload after break - rebuild gradually"
        else:
            # Normal progression
            new_weight = last_weight
            target_reps = min(last_reps + 1, max_reps) if last_reps < max_reps else last_reps
            progression_notes = "Progressive overload - increase reps"
        
        return {
            "sets": len(last_performance.sets),
            "target_reps": target_reps,
            "rep_range": typical_rep_range,
            "weight": round(new_weight, 1) if isinstance(new_weight, (int, float)) else new_weight,
            "rest_seconds": self._calculate_rest_time(exercise_data, recovery_level),
            "progression_notes": progression_notes,
            "volume_unit": "reps_and_weight"
        }
    
    def _program_time_sets(
        self,
        exercise_data: Dict[str, Any],
        last_performance: ExerciseRead | None,
        recovery_level: float
    ) -> Dict[str, Any]:
        """Program sets for time-based exercises"""
        
        typical_time_range = exercise_data.get("typical_rep_range", "30-60s")
        
        if not last_performance or not last_performance.sets:
            # New exercise
            target_duration = 30  # seconds
            sets = 3
        else:
            last_duration = max(set_data.duration_seconds or 0 for set_data in last_performance.sets)
            days_since = self._days_since_performance(last_performance)
            
            if recovery_level >= 85 and days_since <= 3:
                target_duration = last_duration + 5  # Add 5 seconds
                sets = len(last_performance.sets)
            elif recovery_level < 70:
                target_duration = max(last_duration - 10, 20)  # Reduce by 10 seconds
                sets = max(len(last_performance.sets) - 1, 2)
            else:
                target_duration = last_duration
                sets = len(last_performance.sets)
        
        return {
            "sets": sets,
            "target_duration": target_duration,
            "duration_range": typical_time_range,
            "weight": None,
            "rest_seconds": self._calculate_rest_time(exercise_data, recovery_level),
            "progression_notes": f"Hold for {target_duration} seconds per set",
            "volume_unit": "time_based"
        }
    
    def _parse_rep_range(self, rep_range: str) -> tuple[int, int]:
        """Parse rep range string like '8-12' into (min, max)"""
        try:
            if '-' in rep_range:
                min_reps, max_reps = rep_range.split('-')
                return int(min_reps.strip()), int(max_reps.strip())
            else:
                # Single number
                reps = int(rep_range.strip())
                return reps, reps
        except (ValueError, AttributeError):
            # Default fallback
            return 8, 12
    
    def _days_since_performance(self, last_performance: ExerciseRead) -> int:
        """Calculate days since last performance"""
        if last_performance.block and last_performance.block.workout:
            workout_date = last_performance.block.workout.date_created
            return (datetime.now() - workout_date).days
        return 1  # Default to 1 day if no date available
    
    def _calculate_rest_time(self, exercise_data: Dict[str, Any], recovery_level: float) -> int:
        """Calculate appropriate rest time based on exercise and recovery"""
        base_rest = 60  # Default 60 seconds
        
        # Adjust based on exercise intensity
        met_value = exercise_data.get("met_value", 5.0)
        if met_value >= 8:
            base_rest = 90  # High intensity - longer rest
        elif met_value >= 6:
            base_rest = 75  # Moderate intensity
        else:
            base_rest = 60  # Lower intensity
        
        # Adjust based on recovery level
        if recovery_level < 70:
            base_rest += 15  # Poor recovery - longer rest
        elif recovery_level >= 90:
            base_rest -= 10  # Excellent recovery - shorter rest
        
        return max(30, base_rest)  # Minimum 30 seconds rest


# Factory function
def create_set_programming_service() -> SetProgrammingService:
    """Create and return a SetProgrammingService instance"""
    return SetProgrammingService()