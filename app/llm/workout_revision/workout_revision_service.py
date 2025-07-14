from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workout_model import Workout
from app.services.workout_service import get_workout_details
from app.llm.workout_revision.workout_revision_chain import execute_workout_revision_sequence_v2
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm
from app.llm.workout_generation.workout_utils import summarize_training_history
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
from app.llm.workout_generation.workout_parser import parse_compact_workout_to_db_models
from app.llm.utils.db_utils import DatabaseManager
from sqlalchemy.orm import selectinload
import logging

logger = logging.getLogger("workout_revision_service")


def format_workout_for_frontend_preview(workout: Workout) -> Dict[str, Any]:
    """
    Converts a Workout object into a specific dictionary format
    required by the frontend preview screen, especially for sets.
    """
    workout_dict = {
        "name": workout.name,
        "description": workout.description,
        "duration": workout.duration,
        "focus": workout.focus,
        "blocks": []
    }

    if not workout.blocks:
        return workout_dict

    # Use getattr for safety with transient objects
    sorted_blocks = sorted(workout.blocks, key=lambda b: getattr(b, 'position', 0))
    for block in sorted_blocks:
        block_dict = {
            "name": block.name,
            "description": block.description,
            "position": getattr(block, 'position', 0),
            "exercises": []
        }
        
        if not block.exercises:
            workout_dict["blocks"].append(block_dict)
            continue

        sorted_exercises = sorted(block.exercises, key=lambda e: getattr(e, 'position', 0))
        for exercise in sorted_exercises:
            exercise_dict = {
                "name": exercise.name,
                "superset_id": exercise.superset_id,
                "position": getattr(exercise, 'position', 0),
                "sets": []
            }

            if not exercise.sets:
                block_dict["exercises"].append(exercise_dict)
                continue

            sorted_sets = sorted(exercise.sets, key=lambda s: getattr(s, 'position', 0))
            for set_obj in sorted_sets:
                set_dict = {
                    "values": [
                        set_obj.reps,
                        set_obj.weight,
                        set_obj.duration,
                        set_obj.distance,
                        set_obj.rest_time
                    ],
                    "position": getattr(set_obj, 'position', 0)
                }
                exercise_dict["sets"].append(set_dict)
            
            block_dict["exercises"].append(exercise_dict)
        
        workout_dict["blocks"].append(block_dict)

    return workout_dict


def workout_to_dict(workout: Workout) -> Dict[str, Any]:
    """
    Konvertiert ein Workout-Objekt in ein Dictionary für das LLM.
    """
    workout_dict = {
        "id": workout.id,
        "name": workout.name,
        "description": workout.description,
        "duration": workout.duration,
        "focus": workout.focus,
        "notes": workout.notes,
        "date_created": workout.date_created.isoformat() if workout.date_created else None,
        "blocks": []
    }
    
    # Process blocks
    if workout.blocks:
        for block in workout.blocks:
            block_dict = {
                "id": block.id,
                "name": block.name,
                "description": block.description,
                "notes": block.notes,
                "position": getattr(block, "position", 0),
                "is_amrap": getattr(block, "is_amrap", False),
                "amrap_duration_minutes": getattr(block, "amrap_duration_minutes", None),
                "exercises": []
            }
            
            # Process exercises
            if block.exercises:
                for exercise in block.exercises:
                    exercise_dict = {
                        "id": exercise.id,
                        "name": exercise.name,
                        "description": exercise.description,
                        "notes": exercise.notes,
                        "superset_id": exercise.superset_id,
                        "position": getattr(exercise, "position", 0),
                        "sets": []
                    }
                    
                    # Process sets
                    if exercise.sets:
                        for set_obj in exercise.sets:
                            set_dict = {
                                "id": set_obj.id,
                                "weight": set_obj.weight,
                                "reps": set_obj.reps,
                                "duration": set_obj.duration,
                                "distance": set_obj.distance,
                                "rest_time": set_obj.rest_time,
                                "position": getattr(set_obj, "position", 0),
                                "status": set_obj.status.value if hasattr(set_obj.status, 'value') else str(set_obj.status),
                                "completed_at": set_obj.completed_at.isoformat() if set_obj.completed_at else None
                            }
                            exercise_dict["sets"].append(set_dict)
                    
                    block_dict["exercises"].append(exercise_dict)
            
            workout_dict["blocks"].append(block_dict)
    
    return workout_dict


# ============================================================
# V2 Workout Revision Service - Using Proven Workout Generation Pattern
# ============================================================

async def revise_workout_background_v2(
    workout_id: int,
    user_id: str,
    user_feedback: str,
    log_id: int,
):
    """
    ✅ V2: Background task for workout revision using the EXACT same pattern
    as the successful generate_workout_background function.
    
    Pattern:
    1. Gathers all necessary data strings in one DB session
    2. Calls the pure LLM chain function (no DB connection)
    3. Parses the result into DB models using parse_compact_workout_to_db_models
    4. Updates the existing workout in the database
    """
    logger.info(f"[revise_workout_background_v2] Starting for workout_id: {workout_id}")

    # Use the exact same imports as generate_workout_background
    from app.services.llm_logging_service import log_operation_success, log_operation_failed, OperationTimer
    from app.models.training_plan_model import TrainingPlan
    from sqlalchemy import select
    from app.db.session import get_background_session
    from app.llm.workout_generation.workout_utils import summarize_training_history
    from app.db.workout_db_access import get_training_history_for_user_from_db
    from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
    from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm
    from .workout_revision_chain import execute_workout_revision_sequence_v2
    from app.llm.workout_generation.workout_parser import parse_compact_workout_to_db_models

    timer = OperationTimer()
    timer.start()

    user_id_uuid = UUID(user_id)

    try:
        # --- STEP 1: Gather all necessary data in one DB session ---
        formatted_training_plan = None
        summarized_history_str = None
        exercise_library_str = ""
        existing_workout_dict = None
        training_plan_id_for_saving = None

        async with get_background_session() as db:
            logger.info("[revise_workout_background_v2] Loading data from DB...")

            # Load existing workout
            existing_workout_obj = await get_workout_details(
                workout_id=workout_id,
                db=db
            )
            existing_workout_dict = workout_to_dict(existing_workout_obj)
            training_plan_id_for_saving = existing_workout_obj.training_plan_id
            
            # Load and format TrainingPlan (same as workout generation)
            training_plan_db_obj = await db.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
            )
            if training_plan_db_obj:
                formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
                logger.info("[revise_workout_background_v2] Training plan loaded and formatted.")

            # Load, summarize, and format Training History (same as workout generation)
            raw_training_history = await get_training_history_for_user_from_db(
                user_id_uuid, db, limit=10
            )
            if raw_training_history:
                summarized_history_str = summarize_training_history(raw_training_history)
                logger.info("[revise_workout_background_v2] Training history loaded and summarized.")

            # Load exercise library (same as workout generation)
            exercise_library_str = await get_all_exercises_for_prompt(db)
            logger.info(f"[revise_workout_background_v2] Loaded {len(exercise_library_str.splitlines())} exercises.")

        logger.info("[revise_workout_background_v2] DB data gathering complete. Starting LLM revision...")

        # --- STEP 2: Execute LLM revision chain (no DB connection) ---
        compact_workout_schema = await execute_workout_revision_sequence_v2(
            existing_workout=existing_workout_dict,
            user_feedback=user_feedback,
            training_plan_str=formatted_training_plan,
            training_history_str=summarized_history_str,
            exercise_library_str=exercise_library_str,
        )

        logger.info("[revise_workout_background_v2] LLM revision completed. Parsing to frontend-compatible format...")

        # --- STEP 3: Parse the LLM output into a standard Workout model structure ---
        # This creates a transient object tree with the correct field names (e.g., 'duration').
        parsed_workout_obj = parse_compact_workout_to_db_models(
            compact_workout=compact_workout_schema,
            user_id=user_id_uuid,
            training_plan_id=training_plan_id_for_saving,
        )
        
        # Convert the parsed model structure into a dictionary for JSON storage.
        # This dictionary is what the frontend preview screen will use.
        revision_dict = format_workout_for_frontend_preview(parsed_workout_obj)

        logger.info("[revise_workout_background_v2] Parsed workout. Saving to DB...")

        # --- STEP 4: Store revision as JSON instead of direct update ---
        async with get_background_session() as save_db:
            # Load the original workout
            stmt = select(Workout).where(Workout.id == workout_id)
            result = await save_db.execute(stmt)
            original_workout = result.scalar_one_or_none()

            if not original_workout:
                raise ValueError(f"Original workout with ID {workout_id} not found.")

            # Store the frontend-compatible dictionary as JSON
            original_workout.revised_workout_data = revision_dict
            
            save_db.add(original_workout)
            
            logger.info(f"[revise_workout_background_v2] Revised workout stored as JSON for workout {workout_id}.")

        # --- STEP 5: Log success (EXACT same as workout generation) ---
        async with get_background_session() as log_db:
            await log_operation_success(
                db=log_db,
                log_id=log_id,
                duration_ms=timer.get_duration_ms()
            )

        logger.info(f"[revise_workout_background_v2] Completed successfully in {timer.get_duration_ms()}ms")

    except Exception as e:
        logger.error(f"[revise_workout_background_v2] Error: {e}", exc_info=True)
        # Log failure in a separate session (EXACT same as workout generation)
        try:
            async with get_background_session() as error_db:
                await log_operation_failed(
                    db=error_db,
                    log_id=log_id,
                    error_message=str(e),
                    duration_ms=timer.get_duration_ms()
                )
        except Exception as log_e:
            logger.error(f"[revise_workout_background_v2] CRITICAL: Failed to log error: {log_e}")