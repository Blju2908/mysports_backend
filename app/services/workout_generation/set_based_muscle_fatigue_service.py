"""
Set-Based Muscle Fatigue Service

Simplified approach that tracks weekly set volume per muscle group:
- Counts weighted sets per muscle group over rolling 7-day period
- Uses muscle activation percentages to weight each set
- Provides clear progress toward weekly volume targets
- No complex fatigue calculations - just set counting with targets
"""

from typing import List, Dict, Any
from datetime import datetime, timedelta
import json
import os
from enum import Enum

# Import MuscleGroup from archived service
from .archived.volume_based_muscle_fatigue_service import MuscleGroup


class SetBasedMuscleFatigueService:
    """Service for tracking weekly set volume per muscle group"""
    
    # Target weekly sets per muscle group (based on hypertrophy research)
    TARGET_WEEKLY_SETS = {
        # Upper Body - Primary Movers
        MuscleGroup.CHEST.value: 12,              # 3-4 exercises x 3 sets
        MuscleGroup.LATISSIMUS.value: 10,         # Pull exercises
        MuscleGroup.SHOULDERS_ANTERIOR.value: 8,  # Overhead + horizontal push
        MuscleGroup.SHOULDERS_LATERAL.value: 6,   # Lateral raises, etc.
        MuscleGroup.SHOULDERS_POSTERIOR.value: 6, # Rear delt work
        
        # Back
        MuscleGroup.RHOMBOIDS.value: 8,           # Rowing movements
        MuscleGroup.MID_TRAPS.value: 8,           # Rows, shrugs
        MuscleGroup.LOWER_TRAPS.value: 6,         # Pull-ups, Y-raises
        MuscleGroup.UPPER_TRAPS.value: 6,         # Shrugs, upright rows
        MuscleGroup.REAR_DELTS.value: 6,          # Face pulls, reverse flies
        
        # Arms
        MuscleGroup.TRICEPS.value: 9,             # Secondary in push + direct work
        MuscleGroup.BICEPS.value: 8,              # Pull + direct work
        MuscleGroup.FOREARMS.value: 6,            # Grip work, farmer's walks
        
        # Core
        MuscleGroup.RECTUS_ABDOMINIS.value: 8,    # Direct ab work
        MuscleGroup.OBLIQUES.value: 6,            # Side planks, Russian twists
        MuscleGroup.TRANSVERSE_ABDOMINIS.value: 6, # Deep core work
        MuscleGroup.ERECTOR_SPINAE.value: 8,      # Lower back, deadlifts
        
        # Lower Body - Larger muscle groups need more volume
        MuscleGroup.QUADRICEPS.value: 15,         # Squats, lunges, leg press
        MuscleGroup.GLUTES.value: 12,             # Hip dominant movements
        MuscleGroup.HAMSTRINGS.value: 10,         # Deadlifts, RDLs, curls
        MuscleGroup.CALVES.value: 8,              # Calf raises
        MuscleGroup.HIP_FLEXORS.value: 6,         # Hip flexor stretches/strengthening
        MuscleGroup.ADDUCTORS.value: 6,           # Inner thigh work
        MuscleGroup.ABDUCTORS.value: 6,           # Glute med, side steps
    }
    
    def __init__(self):
        self.exercise_descriptions = []
        self._load_exercise_descriptions()
    
    def _load_exercise_descriptions(self):
        """Load exercise descriptions from local JSON file (reuses existing logic)"""
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
        """Find exercise description by English name (reuses existing logic)"""
        for exercise in self.exercise_descriptions:
            if exercise.get("name_english", "").lower() == exercise_name.lower():
                return exercise
        return None
    
    def calculate_weekly_set_progress(
        self, 
        workout_history: List[Dict[str, Any]],
        days_lookback: int = 7
    ) -> Dict[str, Dict[str, float]]:
        """
        Calculate weekly set progress for each muscle group
        
        Args:
            workout_history: List of exercises with completed sets
            days_lookback: Number of days to look back (default: 7 for rolling week)
            
        Returns:
            Dictionary with muscle groups and their set progress:
            {
                "chest": {
                    "current_sets": 8.5,
                    "target_sets": 12,
                    "completion_percentage": 71,
                    "remaining_sets": 3.5
                }
            }
        """
        # Initialize set counts for all muscle groups
        muscle_set_counts = {muscle.value: 0.0 for muscle in MuscleGroup}
        
        cutoff_date = datetime.now() - timedelta(days=days_lookback)
        
        for exercise in workout_history:
            # Find exercise description
            exercise_data = self.find_exercise_description(exercise.get('name', ''))
            if not exercise_data:
                continue
            
            # Process each set that was completed within the lookback period
            for set_data in exercise.get('sets', []):
                if not set_data.get('completed_at'):
                    continue  # Skip incomplete sets
                
                # Parse completed_at and check if within lookback window
                try:
                    completed_at = set_data.get('completed_at')
                    if isinstance(completed_at, str):
                        completed_date = datetime.fromisoformat(completed_at.replace('Z', '+00:00'))
                        if completed_date.tzinfo:
                            completed_date = completed_date.replace(tzinfo=None)
                    else:
                        completed_date = completed_at
                except (ValueError, AttributeError, TypeError):
                    continue
                
                # Skip sets outside lookback window
                if completed_date < cutoff_date:
                    continue
                
                # Distribute this set to muscle groups using muscle_activations
                muscle_activations = exercise_data.get("muscle_activations", [])
                for activation in muscle_activations:
                    muscle_group = activation.get("muscle_group")
                    activation_percentage = activation.get("activation_percentage", 0) / 100
                    
                    # Only count significant muscle activation (>30%)
                    if muscle_group in muscle_set_counts and activation_percentage > 0.3:
                        # Weight the set by activation percentage
                        weighted_set_contribution = 1.0 * activation_percentage
                        muscle_set_counts[muscle_group] += weighted_set_contribution
        
        # Convert to progress format with targets and completion percentages
        return self._format_set_progress_results(muscle_set_counts)
    
    def _format_set_progress_results(self, muscle_set_counts: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Format raw set counts into progress tracking format"""
        results = {}
        
        for muscle_group, current_sets in muscle_set_counts.items():
            target_sets = self.TARGET_WEEKLY_SETS.get(muscle_group, 10)  # Default to 10 if not specified
            
            completion_percentage = min(100.0, (current_sets / target_sets) * 100)
            remaining_sets = max(0.0, target_sets - current_sets)
            
            results[muscle_group] = {
                "current_sets": round(current_sets, 1),
                "target_sets": target_sets,
                "completion_percentage": round(completion_percentage, 1),
                "remaining_sets": round(remaining_sets, 1)
            }
        
        return results
    
    def get_weekly_summary(self, set_progress: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate a summary of weekly training progress"""
        completed_targets = []
        nearly_completed = []  # 80-99%
        moderate_progress = []  # 50-79%
        low_progress = []      # <50%
        
        total_completion = 0.0
        muscle_count = 0
        
        for muscle, progress in set_progress.items():
            completion_pct = progress["completion_percentage"]
            total_completion += completion_pct
            muscle_count += 1
            
            if completion_pct >= 100:
                completed_targets.append(muscle)
            elif completion_pct >= 80:
                nearly_completed.append(muscle)
            elif completion_pct >= 50:
                moderate_progress.append(muscle)
            else:
                low_progress.append(muscle)
        
        avg_completion = total_completion / muscle_count if muscle_count > 0 else 0
        
        return {
            "completed_targets": completed_targets,
            "nearly_completed": nearly_completed,
            "moderate_progress": moderate_progress, 
            "low_progress": low_progress,
            "overall_completion_avg": round(avg_completion, 1),
            "muscles_at_target": len(completed_targets),
            "total_muscle_groups": muscle_count
        }
    
    def get_recommended_muscle_groups(self, set_progress: Dict[str, Dict[str, float]], limit: int = 3) -> List[Dict[str, Any]]:
        """Get recommended muscle groups to train based on lowest completion percentages"""
        # Sort muscle groups by completion percentage (ascending)
        sorted_muscles = sorted(
            set_progress.items(), 
            key=lambda x: x[1]["completion_percentage"]
        )
        
        recommendations = []
        for muscle, progress in sorted_muscles[:limit]:
            recommendations.append({
                "muscle_group": muscle,
                "current_sets": progress["current_sets"],
                "target_sets": progress["target_sets"],
                "remaining_sets": progress["remaining_sets"],
                "completion_percentage": progress["completion_percentage"],
                "priority": "high" if progress["completion_percentage"] < 50 else "medium"
            })
        
        return recommendations


# Factory function for easy importing
def create_set_based_muscle_fatigue_service() -> SetBasedMuscleFatigueService:
    """Create and return a SetBasedMuscleFatigueService instance"""
    return SetBasedMuscleFatigueService()