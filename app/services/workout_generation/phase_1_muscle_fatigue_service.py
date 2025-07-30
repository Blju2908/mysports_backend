"""
Phase 1: Muscle Fatigue Analysis Service

Calculate evidence-based muscle recovery percentages using:
- Workout history from database
- Exercise descriptions (initially from local JSON, later from database)
- Volume-based fatigue calculation with muscle activation data
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json
import os
from enum import Enum

from app.schemas.workout_schema import Phase1ExerciseRead


class MuscleGroup(str, Enum):
    """Normalized muscle groups for consistent mapping"""
    
    # Upper Body
    CHEST = "chest"
    SHOULDERS_ANTERIOR = "shoulders_anterior"
    SHOULDERS_LATERAL = "shoulders_lateral"
    SHOULDERS_POSTERIOR = "shoulders_posterior"
    TRICEPS = "triceps"
    BICEPS = "biceps"
    FOREARMS = "forearms"
    
    # Back
    LATISSIMUS = "latissimus"
    RHOMBOIDS = "rhomboids"
    MID_TRAPS = "mid_traps"
    LOWER_TRAPS = "lower_traps"
    UPPER_TRAPS = "upper_traps"
    REAR_DELTS = "rear_delts"
    
    # Core
    RECTUS_ABDOMINIS = "rectus_abdominis"
    OBLIQUES = "obliques"
    TRANSVERSE_ABDOMINIS = "transverse_abdominis"
    ERECTOR_SPINAE = "erector_spinae"
    
    # Lower Body
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    HIP_FLEXORS = "hip_flexors"
    ADDUCTORS = "adductors"
    ABDUCTORS = "abductors"


class MuscleFatigueService:
    """Service for calculating muscle fatigue and recovery percentages"""
    
    def __init__(self):
        self.exercise_descriptions = []
        self._load_exercise_descriptions()
    
    def _load_exercise_descriptions(self):
        """Load exercise descriptions from local JSON file"""
        try:
            file_path = os.path.join(
                os.path.dirname(__file__), 
                "data", 
                "sample_exercise_descriptions.json"
            )
            with open(file_path, 'r', encoding='utf-8') as f:
                self.exercise_descriptions = json.load(f)
        except FileNotFoundError:
            print(f"Exercise descriptions file not found at {file_path}")
            self.exercise_descriptions = []
        except json.JSONDecodeError as e:
            print(f"Error parsing exercise descriptions JSON: {e}")
            self.exercise_descriptions = []
    
    def find_exercise_description(self, exercise_name: str) -> Dict[str, Any] | None:
        """Find exercise description by English name only"""
        for exercise in self.exercise_descriptions:
            if exercise.get("name_english", "").lower() == exercise_name.lower():
                return exercise
        return None
    
    def calculate_muscle_fatigue(
        self, 
        workout_history: List[Phase1ExerciseRead],
        days_lookback: int = 14
    ) -> Dict[str, float]:
        """
        Calculate muscle fatigue based on workout history and exercise descriptions
        
        Args:
            workout_history: List of exercises with completed sets
            days_lookback: Number of days to look back for fatigue calculation
            
        Returns:
            Dictionary with muscle groups and recovery percentages (0-100)
        """
        # Initialize fatigue scores for all muscle groups
        fatigue_scores = {muscle.value: 0.0 for muscle in MuscleGroup}
        
        cutoff_date = datetime.now() - timedelta(days=days_lookback)
        
        for exercise in workout_history:
            # Find exercise description
            exercise_data = self.find_exercise_description(exercise.name)
            if not exercise_data:
                continue
            
            # Apply recovery complexity modifier
            complexity_modifier = {
                "low": 1.0, 
                "medium": 1.2, 
                "high": 1.4, 
                "very_high": 1.6
            }.get(exercise_data.get("recovery_complexity", "medium"), 1.2)
            
            # Process each set individually using its completed_at timestamp
            for set_data in exercise.sets:
                if not set_data.completed_at:
                    continue  # Skip incomplete sets
                
                # Parse completed_at and check if within lookback window
                try:
                    if isinstance(set_data.completed_at, str):
                        completed_date = datetime.fromisoformat(set_data.completed_at.replace('Z', '+00:00'))
                        if completed_date.tzinfo:
                            completed_date = completed_date.replace(tzinfo=None)
                    else:
                        completed_date = set_data.completed_at
                except (ValueError, AttributeError):
                    continue
                
                # Skip sets outside lookback window
                if completed_date < cutoff_date:
                    continue
                
                days_ago = (datetime.now() - completed_date).days
                
                # Calculate volume for this specific set
                set_volume = self._calculate_set_volume(set_data, exercise_data)
                
                # Apply time-based decay (30% daily recovery baseline)
                decay_factor = 0.7 ** days_ago
                
                # Distribute fatigue to muscle groups using muscle_activations
                muscle_activations = exercise_data.get("muscle_activations", [])
                for activation in muscle_activations:
                    muscle_group = activation.get("muscle_group")
                    activation_percentage = activation.get("activation_percentage", 0) / 100
                    
                    if muscle_group in fatigue_scores:
                        fatigue_contribution = (
                            set_volume * activation_percentage * decay_factor * complexity_modifier
                        )
                        fatigue_scores[muscle_group] += fatigue_contribution
        
        # Convert fatigue scores to recovery percentages
        return self._convert_to_recovery_percentages(fatigue_scores)
    
    def _calculate_set_volume(self, set_data, exercise_data: Dict[str, Any]) -> float:
        """Calculate volume for a single set based on volume_unit"""
        volume_unit = exercise_data.get("volume_unit", "reps_only")
        muscle_fatigue_factor = exercise_data.get("muscle_fatigue_factor", 1.0)
        met_value = exercise_data.get("met_value", 5.0)
        
        if volume_unit == "reps_only":
            reps = set_data.reps or 0
            return reps * muscle_fatigue_factor
        
        elif volume_unit == "reps_and_weight":
            reps = set_data.reps or 0
            weight = set_data.weight or 0
            return (reps * weight) * met_value / 100  # Scale down weight-based volume
        
        elif volume_unit == "time_based":
            duration = set_data.duration or 0  # Fixed: use duration instead of duration_seconds
            return duration * met_value / 60  # Convert to minutes and scale
        
        elif volume_unit == "distance_based":
            # Use distance if available, otherwise fallback to reps
            distance = getattr(set_data, 'distance', None) or set_data.reps or 0
            return distance * met_value
        
        return 0.0
    
    def _convert_to_recovery_percentages(self, fatigue_scores: Dict[str, float]) -> Dict[str, float]:
        """Convert fatigue scores to recovery percentages (0-100)"""
        max_fatigue_threshold = 1000.0
        
        recovery_percentages = {}
        for muscle, score in fatigue_scores.items():
            # Higher fatigue score = lower recovery percentage
            recovery_pct = max(0, 100 - min(100, (score / max_fatigue_threshold) * 100))
            recovery_percentages[muscle] = round(recovery_pct, 1)
        
        return recovery_percentages
    
    def get_muscle_recovery_summary(self, recovery_percentages: Dict[str, float]) -> Dict[str, Any]:
        """Generate a summary of muscle recovery status"""
        well_recovered = []
        moderately_recovered = []
        poorly_recovered = []
        
        for muscle, recovery in recovery_percentages.items():
            if recovery >= 85:
                well_recovered.append(muscle)
            elif recovery >= 70:
                moderately_recovered.append(muscle)
            else:
                poorly_recovered.append(muscle)
        
        return {
            "well_recovered": well_recovered,
            "moderately_recovered": moderately_recovered, 
            "poorly_recovered": poorly_recovered,
            "overall_recovery_avg": round(sum(recovery_percentages.values()) / len(recovery_percentages), 1)
        }


# Factory function for easy importing
def create_muscle_fatigue_service() -> MuscleFatigueService:
    """Create and return a MuscleFatigueService instance"""
    return MuscleFatigueService()