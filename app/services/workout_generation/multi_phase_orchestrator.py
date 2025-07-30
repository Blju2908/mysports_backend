"""
Multi-Phase Workout Generation Orchestrator

Main coordinator service that orchestrates the 5-phase workout generation system:
1. Muscle Fatigue Analysis (Code-based)
2. Workout Focus Determination (LLM-assisted)  
3. Exercise Filtering (Code-based)
4. Workout Creation (LLM-creative)
5. Set Programming (Code-based)

Integrates with existing database infrastructure and follows established patterns.
"""

from uuid import UUID
from typing import Dict, Any, List
from sqlmodel import select

from app.db.session import get_background_session
from app.services.workout_service import get_exercises_with_done_sets_only
from app.schemas.workout_schema import ExerciseRead
from app.schemas.exercise_description_schema import ExerciseDescriptionRead
from app.models.exercise_description_model import ExerciseDescription

from .phase_1_muscle_fatigue_service import create_muscle_fatigue_service
from .phase_2_workout_focus_service import create_workout_focus_service
from .phase_3_exercise_filtering_service import create_exercise_filtering_service
from .phase_4_workout_creation_service import create_workout_creation_service
from .phase_5_set_programming_service import create_set_programming_service


async def create_multi_phase_workout(
    user_id: UUID, 
    session_duration: int = 60, 
    profile_id: int = 1,
    user_prompt: str = "",
    available_equipment: List[str] = None
) -> Dict[str, Any]:
    """
    Main entry point for multi-phase workout generation
    
    Args:
        user_id: User's UUID
        session_duration: Available workout time in minutes
        profile_id: Training profile ID (for future use)
        user_prompt: Specific user requests
        available_equipment: User's available equipment list
        
    Returns:
        Complete workout structure with all phases' outputs
    """
    
    # Load necessary data from database
    training_history_dtos, exercise_descriptions_dtos = await load_workout_creation_data(user_id)
    
    # Initialize services
    fatigue_service = create_muscle_fatigue_service()
    focus_service = create_workout_focus_service()
    filtering_service = create_exercise_filtering_service()
    creation_service = create_workout_creation_service()
    programming_service = create_set_programming_service()
    
    # === PHASE 1: MUSCLE FATIGUE ANALYSIS ===
    print("🔍 Phase 1: Analyzing muscle fatigue...")
    recovery_percentages = fatigue_service.calculate_muscle_fatigue(
        workout_history=training_history_dtos,
        days_lookback=14
    )
    recovery_summary = fatigue_service.get_muscle_recovery_summary(recovery_percentages)
    
    print(f"Recovery Analysis: {recovery_summary['overall_recovery_avg']}% average recovery")
    print(f"Well recovered: {len(recovery_summary['well_recovered'])} muscle groups")
    print(f"Poorly recovered: {len(recovery_summary['poorly_recovered'])} muscle groups")
    
    # === PHASE 2: WORKOUT FOCUS DETERMINATION ===
    print("🧠 Phase 2: Determining workout focus...")
    workout_focus = focus_service.determine_workout_focus(
        recovery_percentages=recovery_percentages,
        user_goals="general_fitness",  # TODO: Get from user profile
        session_duration=session_duration,
        user_prompt=user_prompt,
        days_since_last_workout=1  # TODO: Calculate from last workout
    )
    
    print(f"Workout Focus: {workout_focus.workout_type} - {workout_focus.movement_focus}")
    print(f"Target muscles: {workout_focus.primary_muscles}")
    print(f"Avoid muscles: {workout_focus.avoid_muscles}")
    
    # === PHASE 3: EXERCISE FILTERING ===
    print("⚡ Phase 3: Filtering exercises...")
    
    # Convert exercise descriptions to local format for filtering
    # (For now, use local JSON. Later will use database exercise descriptions)
    filtered_exercises = filtering_service.filter_exercises(
        exercise_descriptions=fatigue_service.exercise_descriptions,  # Using local JSON
        workout_focus=workout_focus,
        recovery_percentages=recovery_percentages,
        available_equipment=available_equipment or [],
        min_recovery_threshold=70.0
    )
    
    filtering_summary = filtering_service.get_filtering_summary(
        original_count=len(fatigue_service.exercise_descriptions),
        filtered_count=len(filtered_exercises),
        workout_focus=workout_focus
    )
    
    print(f"Exercise Filtering: {filtering_summary['filtering_efficiency']}")
    print(f"Reduction: {filtering_summary['reduction_percentage']}%")
    
    # === PHASE 4: WORKOUT CREATION ===
    print("🎨 Phase 4: Creating workout structure...")
    workout_structure = creation_service.create_workout(
        filtered_exercises=filtered_exercises,
        workout_focus=workout_focus,
        session_duration=session_duration,
        user_prompt=user_prompt
    )
    
    print(f"Created workout: {workout_structure.workout_name}")
    print(f"Exercise blocks: {len(workout_structure.exercise_blocks)}")
    print(f"Estimated duration: {workout_structure.estimated_duration} minutes")
    
    # === PHASE 5: SET PROGRAMMING ===
    print("📊 Phase 5: Programming sets and reps...")
    
    # Program each exercise in the workout
    programmed_exercises = []
    for block in workout_structure.exercise_blocks:
        exercise_name = block.get("exercise_name", "")
        
        # Find the exercise data
        exercise_data = None
        for ex in filtered_exercises:
            if ex.get("name_german", "").lower() == exercise_name.lower():
                exercise_data = ex
                break
        
        if exercise_data:
            # Calculate recovery level for this exercise's primary muscles
            primary_muscles = [
                act["muscle_group"] for act in exercise_data.get("muscle_activations", [])
                if act.get("activation_percentage", 0) >= 50
            ]
            avg_recovery = sum(recovery_percentages.get(muscle, 100) for muscle in primary_muscles) / len(primary_muscles) if primary_muscles else 85
            
            # Program the sets
            set_programming = programming_service.program_exercise_sets(
                exercise_data=exercise_data,
                workout_history=training_history_dtos,
                recovery_level=avg_recovery
            )
            
            # Merge programming into block
            block.update({
                "sets": set_programming.get("sets", 3),
                "reps": set_programming.get("rep_range", set_programming.get("target_reps", "8-12")),
                "weight": set_programming.get("weight"),
                "rest_seconds": set_programming.get("rest_seconds", 60),
                "progression_notes": set_programming.get("progression_notes", ""),
                "volume_unit": set_programming.get("volume_unit", "reps_only")
            })
        
        programmed_exercises.append(block)
    
    print(f"Programmed {len(programmed_exercises)} exercises with sets/reps")
    
    # === COMPILE FINAL RESULT ===
    result = {
        "success": True,
        "workout_structure": {
            "name": workout_structure.workout_name,
            "duration": workout_structure.estimated_duration,
            "exercises": programmed_exercises,
            "warm_up": workout_structure.warm_up_exercises,
            "cool_down": workout_structure.cool_down_exercises,
            "notes": workout_structure.workout_notes
        },
        "phase_data": {
            "phase_1_recovery": {
                "muscle_recovery_percentages": recovery_percentages,
                "recovery_summary": recovery_summary
            },
            "phase_2_focus": {
                "primary_muscles": workout_focus.primary_muscles,
                "avoid_muscles": workout_focus.avoid_muscles,
                "workout_type": workout_focus.workout_type,
                "intensity": workout_focus.intensity,
                "rationale": workout_focus.rationale
            },
            "phase_3_filtering": filtering_summary,
            "phase_4_creation": {
                "selected_exercises": len(workout_structure.exercise_blocks),
                "workout_theme": workout_focus.movement_focus
            },
            "phase_5_programming": {
                "programmed_exercises": len(programmed_exercises),
                "average_rest_time": sum(ex.get("rest_seconds", 60) for ex in programmed_exercises) / len(programmed_exercises) if programmed_exercises else 60
            }
        },
        "meta": {
            "generation_method": "multi_phase_v1",
            "phases_completed": 5,
            "data_sources": {
                "workout_history": len(training_history_dtos),
                "exercise_descriptions": len(fatigue_service.exercise_descriptions)
            }
        }
    }
    
    print("✅ Multi-phase workout generation completed successfully!")
    return result


async def load_workout_creation_data(user_id: UUID):
    """
    Load workout creation data - using JSON file temporarily until DB structure is ready
    """
    import json
    import os
    from pathlib import Path
    from datetime import datetime, timedelta
    
    # Load Training History from database
    async with get_background_session() as db_session:
        training_history_db = await get_exercises_with_done_sets_only(
            db_session, 
            user_id, 
            number_of_workouts=10
        )
        training_history_dtos = [
            ExerciseRead.model_validate(exercise) 
            for exercise in training_history_db
        ]
    
    # Load Exercise Descriptions from JSON file (temporary)
    json_file_path = Path(__file__).parent / "data" / "sample_exercise_descriptions.json"
    
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            exercise_data = json.load(f)
        
        # Convert JSON data to ExerciseDescriptionRead DTOs
        exercise_descriptions_dtos = []
        for i, exercise in enumerate(exercise_data):
            # Create a temporary DTO structure that matches what the system expects
            dto_data = {
                "id": i + 1,  # Temporary ID
                "name_german": exercise["name_german"],
                "name_english": exercise["name_english"],
                "aliases": exercise.get("aliases", []),
                "description_german": exercise["description_german"],
                "exercise_type": exercise["exercise_type"],
                "difficulty_level": exercise["difficulty_level"],
                "movement_pattern": exercise["movement_pattern"],
                "is_unilateral": exercise["is_unilateral"],
                "is_compound": exercise["is_compound"],
                "muscle_activations": exercise["muscle_activations"],
                "equipment_list": exercise["equipment_list"],
                "setup_steps": exercise["setup_steps"],
                "execution_steps": exercise["execution_steps"],
                "common_mistakes": exercise["common_mistakes"],
                "volume_unit": exercise["volume_unit"],
                "typical_rep_range": exercise["typical_rep_range"],
                "met_value": exercise["met_value"],
                "muscle_fatigue_factor": exercise["muscle_fatigue_factor"],
                "muscle_recovery_hours": exercise["muscle_recovery_hours"],
                "recovery_complexity": exercise["recovery_complexity"],
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            }
            exercise_descriptions_dtos.append(ExerciseDescriptionRead.model_validate(dto_data))
            
    except FileNotFoundError:
        print(f"Warning: JSON file not found at {json_file_path}")
        exercise_descriptions_dtos = []
    except Exception as e:
        print(f"Error loading exercise descriptions from JSON: {e}")
        exercise_descriptions_dtos = []
    
    return training_history_dtos, exercise_descriptions_dtos


# Convenience function for backwards compatibility
async def create_workout_main_flow(user_id: UUID, session_duration: int, profile_id: int):
    """
    Backwards compatible entry point that maintains the same signature
    as the original create_workout_service.py
    """
    return await create_multi_phase_workout(
        user_id=user_id,
        session_duration=session_duration,
        profile_id=profile_id
    )