from typing import Dict, Any, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.workout_model import Workout
from app.services.workout_service import get_workout_details
from app.llm.workout_revision.workout_revision_chain import revise_workout_two_step
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm


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





async def run_workout_revision_chain(
    workout_id: int,
    user_feedback: str,
    user_id: Optional[UUID] = None,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> WorkoutSchema:
    """
    Führt die Workout-Revision Chain aus.
    
    Args:
        workout_id: ID des zu überarbeitenden Workouts
        user_feedback: Feedback/Kommentar des Users
        user_id: Optional - User ID für zusätzlichen Kontext und Laden des Trainingsplans
        training_plan: Optional - Trainingsplan als String (wird automatisch geladen und formatiert wenn user_id gegeben)
        training_history: Optional - Trainingshistorie als JSON-String
        db: Database Session
        
    Returns:
        WorkoutSchema: Das überarbeitete Workout
    """
    if not db:
        raise ValueError("Database session is required")
    
    try:
        # 1. Lade den Trainingsplan aus der DB wenn user_id gegeben ist
        formatted_training_plan = training_plan
        
        if user_id is not None:
            # Get training plan from the user
            # ✅ SQLModel One-Liner: Direkt TrainingPlan über user_id laden
            training_plan_db_obj = await db.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id)
            )
            if training_plan_db_obj:
                formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
        
        # 2. Lade das bestehende Workout aus der Datenbank
        existing_workout_obj = await get_workout_details(
            workout_id=workout_id,
            db=db
        )
        
        # 3. Konvertiere das Workout in ein Dictionary für das LLM
        existing_workout_dict = workout_to_dict(existing_workout_obj)
        
        # 4. Führe die Revision Chain aus (2-Stufen)
        revised_workout_schema = await revise_workout_two_step(
            existing_workout=existing_workout_dict,
            user_feedback=user_feedback,
            training_plan=formatted_training_plan,
            training_history=training_history
        )
        
        return revised_workout_schema
        
    except Exception as e:
        print(f"Error in run_workout_revision_chain: {e}")
        import traceback
        traceback.print_exc()
        raise


async def get_workout_for_revision(
    workout_id: int,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    Lädt ein Workout für die Revision und gibt es als Dictionary zurück.
    
    Args:
        workout_id: ID des Workouts
        db: Database Session
        
    Returns:
        Dict: Workout als Dictionary
    """
    try:
        workout_obj = await get_workout_details(
            workout_id=workout_id,
            db=db
        )
        
        return workout_to_dict(workout_obj)
        
    except Exception as e:
        print(f"Error in get_workout_for_revision: {e}")
        raise 