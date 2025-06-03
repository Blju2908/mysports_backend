import json
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from app.services.workout_service import get_workout_details
from app.llm.workout_revision.workout_revision_chain import revise_workout
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema


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
                                "status": set_obj.status.value if hasattr(set_obj.status, 'value') else str(set_obj.status),
                                "completed_at": set_obj.completed_at.isoformat() if set_obj.completed_at else None
                            }
                            exercise_dict["sets"].append(set_dict)
                    
                    block_dict["exercises"].append(exercise_dict)
            
            workout_dict["blocks"].append(block_dict)
    
    return workout_dict


async def save_revised_workout(
    workout_id: int,
    revised_workout_schema: WorkoutSchema,
    db: AsyncSession
) -> Workout:
    """
    Speichert das überarbeitete Workout in der Datenbank und ersetzt das ursprüngliche.
    
    Args:
        workout_id: ID des zu ersetzenden Workouts
        revised_workout_schema: Das überarbeitete Workout Schema
        db: Database Session
        
    Returns:
        Workout: Das gespeicherte Workout-Objekt
    """
    try:
        # 1. Lade das bestehende Workout mit allen Beziehungen
        workout_query = (
            select(Workout)
            .options(
                selectinload(Workout.blocks)
                .selectinload(Block.exercises)
                .selectinload(Exercise.sets)
            )
            .where(Workout.id == workout_id)
        )
        result = await db.execute(workout_query)
        existing_workout = result.scalar_one_or_none()
        
        if not existing_workout:
            raise ValueError(f"Workout with ID {workout_id} not found")
        
        # 2. Lösche alle bestehenden Blöcke, Übungen und Sets (Cascade Delete)
        for block in existing_workout.blocks:
            await db.delete(block)
        
        # 3. Aktualisiere die Workout-Details
        existing_workout.name = revised_workout_schema.name
        existing_workout.description = revised_workout_schema.description
        existing_workout.duration = revised_workout_schema.duration
        existing_workout.focus = revised_workout_schema.focus
        
        # 4. Erstelle neue Blöcke, Übungen und Sets basierend auf dem revidierten Schema
        for block_schema in revised_workout_schema.blocks:
            new_block = Block(
                workout_id=existing_workout.id,
                name=block_schema.name,
                description=block_schema.description
            )
            db.add(new_block)
            await db.flush()  # Get block ID
            
            for exercise_schema in block_schema.exercises:
                new_exercise = Exercise(
                    block_id=new_block.id,
                    name=exercise_schema.name,
                    description=exercise_schema.description,
                    superset_id=exercise_schema.superset_id
                )
                db.add(new_exercise)
                await db.flush()  # Get exercise ID
                
                for set_schema in exercise_schema.sets:
                    # Parse the values array: [weight, reps, duration, distance, rest_time]
                    values = set_schema.values if hasattr(set_schema, 'values') else []
                    
                    weight = values[0] if len(values) > 0 and isinstance(values[0], (int, float)) else None
                    reps = values[1] if len(values) > 1 and isinstance(values[1], (int, float)) else None
                    duration = values[2] if len(values) > 2 and isinstance(values[2], (int, float)) else None
                    distance = values[3] if len(values) > 3 and isinstance(values[3], (int, float)) else None
                    rest_time = values[4] if len(values) > 4 and isinstance(values[4], (int, float)) else None
                    
                    new_set = Set(
                        exercise_id=new_exercise.id,
                        weight=weight,
                        reps=int(reps) if reps is not None else None,
                        duration=int(duration) if duration is not None else None,
                        distance=distance,
                        rest_time=int(rest_time) if rest_time is not None else None,
                        status=SetStatus.open  # All sets start as open
                    )
                    db.add(new_set)
        
        await db.commit()
        await db.refresh(existing_workout)
        
        # 5. Lade das aktualisierte Workout mit allen Beziehungen
        updated_workout = await get_workout_details(workout_id=workout_id, db=db)
        return updated_workout
        
    except Exception as e:
        await db.rollback()
        print(f"Error in save_revised_workout: {e}")
        import traceback
        traceback.print_exc()
        raise


async def run_workout_revision_chain(
    workout_id: int,
    user_feedback: str,
    user_id: Optional[str] = None,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    db: Optional[AsyncSession] = None
) -> WorkoutSchema:
    """
    Führt die Workout-Revision Chain aus.
    
    Args:
        workout_id: ID des zu überarbeitenden Workouts
        user_feedback: Feedback/Kommentar des Users
        user_id: Optional - User ID für zusätzlichen Kontext
        training_plan: Optional - Trainingsplan als String
        training_history: Optional - Trainingshistorie als JSON-String
        db: Database Session
        
    Returns:
        WorkoutSchema: Das überarbeitete Workout
    """
    if not db:
        raise ValueError("Database session is required")
    
    try:
        # 1. Lade das bestehende Workout aus der Datenbank
        existing_workout_obj = await get_workout_details(
            workout_id=workout_id,
            db=db
        )
        
        # 2. Konvertiere das Workout in ein Dictionary für das LLM
        existing_workout_dict = workout_to_dict(existing_workout_obj)
        
        # 3. Führe die Revision Chain aus
        revised_workout_schema = await revise_workout(
            existing_workout=existing_workout_dict,
            user_feedback=user_feedback,
            training_plan=training_plan,
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