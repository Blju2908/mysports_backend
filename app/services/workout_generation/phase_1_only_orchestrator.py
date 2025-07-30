"""
Phase 1 Only Orchestrator - Simplified version for testing

This orchestrator only runs Phase 1 (Muscle Fatigue Analysis) using local JSON data
for both training history and exercise descriptions.
"""

from uuid import UUID
from typing import Dict, Any, List
import json
from pathlib import Path
from datetime import datetime

from app.schemas.workout_schema import Phase1ExerciseRead, Phase1SetRead, Phase1WorkoutRead
from app.schemas.exercise_description_schema import Phase1ExerciseDescriptionRead
from .phase_1_muscle_fatigue_service import create_muscle_fatigue_service


def load_local_training_history(user_id: UUID) -> List[Phase1ExerciseRead]:
    """
    Load training history from local JSON file
    """
    json_file_path = Path(__file__).parent / "data" / "sample_training_history.json"
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            workouts_data = json.load(f)
        
        # Convert to Phase1ExerciseRead DTOs (flattened structure for muscle fatigue analysis)
        exercises = []
        
        for workout in workouts_data:
            # Only include workouts for the specified user
            if workout["user_id"] != str(user_id):
                continue
                
            for block in workout.get("blocks", []):
                for exercise in block.get("exercises", []):
                    # Process sets and add exercise_id
                    processed_sets = []
                    for set_data in exercise.get("sets", []):
                        set_with_exercise_id = set_data.copy()
                        set_with_exercise_id["exercise_id"] = exercise["id"]
                        processed_sets.append(Phase1SetRead.model_validate(set_with_exercise_id))
                    
                    # Create a flattened exercise structure for muscle fatigue analysis
                    exercise_dto = {
                        "id": exercise["id"],
                        "name": exercise["name"],
                        "description": exercise.get("description", ""),
                        "notes": exercise.get("notes", ""),
                        "superset_id": exercise.get("superset_id"),
                        "position": exercise.get("position", 0),
                        "block_id": block["id"],
                        "workout_id": workout["id"],
                        "workout_name": workout["name"],
                        "workout_date": workout["date_created"],
                        "workout_focus": workout.get("focus"),
                        "sets": processed_sets  # Use processed sets with exercise_id
                    }
                    exercises.append(Phase1ExerciseRead.model_validate(exercise_dto))
        
        print(f"✅ Loaded {len(exercises)} exercises from {len(workouts_data)} workouts")
        return exercises
        
    except FileNotFoundError:
        print(f"❌ Training history file not found at {json_file_path}")
        return []
    except Exception as e:
        print(f"❌ Error loading training history: {e}")
        return []


def load_local_exercise_descriptions() -> List[Phase1ExerciseDescriptionRead]:
    """
    Load exercise descriptions from local JSON file
    """
    json_file_path = Path(__file__).parent / "data" / "sample_exercise_descriptions.json"
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            exercise_data = json.load(f)
        
        # Convert JSON data to Phase1ExerciseDescriptionRead DTOs (flexible parsing)
        exercise_descriptions_dtos = []
        for exercise in exercise_data:
            try:
                # The Phase1ExerciseDescriptionRead schema is flexible and handles optional fields
                exercise_descriptions_dtos.append(Phase1ExerciseDescriptionRead.model_validate(exercise))
            except Exception as e:
                print(f"⚠️  Warning: Could not parse exercise '{exercise.get('name_german', 'Unknown')}': {e}")
                # Continue with other exercises rather than failing completely
        
        print(f"✅ Loaded {len(exercise_descriptions_dtos)} exercise descriptions")
        return exercise_descriptions_dtos
        
    except FileNotFoundError:
        print(f"❌ Exercise descriptions file not found at {json_file_path}")
        return []
    except Exception as e:
        print(f"❌ Error loading exercise descriptions: {e}")
        return []


def find_exercise_description_by_name(
    exercise_name: str, 
    exercise_descriptions: List[Phase1ExerciseDescriptionRead]
) -> Phase1ExerciseDescriptionRead:
    """
    Find exercise description by name with fallback behavior
    """
    # Try exact match first (English - primary)
    for desc in exercise_descriptions:
        if desc.name_english.lower() == exercise_name.lower():
            return desc
    
    # Try exact match (German - if available)
    for desc in exercise_descriptions:
        if desc.name_german and desc.name_german.lower() == exercise_name.lower():
            return desc
    
    # Try aliases
    for desc in exercise_descriptions:
        for alias in desc.aliases:
            if alias.lower() == exercise_name.lower():
                return desc
    
    # Try partial matches
    for desc in exercise_descriptions:
        if (exercise_name.lower() in desc.name_german.lower() or 
            exercise_name.lower() in desc.name_english.lower()):
            return desc
    
    # Fallback: Create a default exercise description
    print(f"⚠️  Exercise '{exercise_name}' not found in descriptions, using fallback")
    
    # Create a basic fallback with generic muscle activation
    fallback_dto_data = {
        "name_german": exercise_name,
        "name_english": exercise_name,
        "description_german": f"Übung: {exercise_name}",
        "difficulty_level": "intermediate",
        "is_unilateral": False,
        "primary_movement_pattern": "compound",
        "target_muscle_groups": ["chest", "shoulders_anterior", "triceps"],
        "muscle_activations": [
            {"muscle_group": "chest", "activation_percentage": 50},
            {"muscle_group": "shoulders_anterior", "activation_percentage": 30},
            {"muscle_group": "triceps", "activation_percentage": 40}
        ],
        "equipment_list": [],
        "execution_steps": ["Führe die Bewegung kontrolliert aus"],
        "muscle_fatigue_factor": 1.0,
        "muscle_recovery_hours": 48,
        "recovery_complexity": "medium"
    }
    
    return Phase1ExerciseDescriptionRead.model_validate(fallback_dto_data)


async def run_phase_1_only(
    user_id: UUID, 
    days_lookback: int = 14
) -> Dict[str, Any]:
    """
    Run only Phase 1 (Muscle Fatigue Analysis) using local data
    
    Args:
        user_id: User's UUID
        days_lookback: Number of days to look back for muscle fatigue analysis
        
    Returns:
        Phase 1 results with muscle recovery data
    """
    # === LOAD LOCAL DATA ===
    training_history = load_local_training_history(user_id)
    exercise_descriptions = load_local_exercise_descriptions()
    
    if not training_history:
        return {"success": False, "error": "No training history available"}
    
    # === ENHANCE TRAINING HISTORY WITH EXERCISE DESCRIPTIONS ===
    enhanced_training_history = []
    
    for exercise in training_history:
        # Find matching exercise description (with fallback)
        exercise_description = find_exercise_description_by_name(
            exercise.name, 
            exercise_descriptions
        )
        
        # Add exercise description data to the exercise
        enhanced_exercise = exercise.model_copy()
        enhanced_exercise.exercise_description = exercise_description
        enhanced_training_history.append(enhanced_exercise)
    
    # === PHASE 1: MUSCLE FATIGUE ANALYSIS ===
    
    fatigue_service = create_muscle_fatigue_service()
    recovery_percentages = fatigue_service.calculate_muscle_fatigue(
        workout_history=enhanced_training_history,
        days_lookback=days_lookback
    )
    
    recovery_summary = fatigue_service.get_muscle_recovery_summary(recovery_percentages)
    avg_recovery = recovery_summary["overall_recovery_avg"]
    
    
    # === COMPILE RESULT ===
    result = {
        "success": True,
        "phase_1_results": {
            "muscle_recovery_percentages": recovery_percentages,
            "recovery_summary": recovery_summary,
            "average_recovery": avg_recovery
        },
        "data_sources": {
            "training_history_exercises": len(training_history),
            "exercise_descriptions": len(exercise_descriptions),
            "days_analyzed": days_lookback
        },
        "meta": {
            "generation_method": "phase_1_only",
            "phases_completed": 1,
            "user_id": str(user_id),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    print("\n✅ Phase 1 completed successfully!")
    return result