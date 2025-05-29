from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime

from app.db.trainingplan_db_access import get_training_plan_for_user
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.workout_generation_chain import generate_workout
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus

async def run_workout_chain(
    user_id: UUID | None,
    user_prompt: str | None,
    db: AsyncSession,
    save_to_db: bool = False,
) -> Any:
    """
    Führt den Workout-Generierungs-Prozess mit dem LLM durch.
    Lädt die letzten 10 Workouts des Users als Trainingshistorie.

    Args:
        user_id: Die ID des Benutzers.
        user_prompt: Ein optionaler Prompt des Benutzers.
        db: Die Datenbankverbindung.
        save_to_db: Wenn True, wird das Workout in der DB gespeichert und das Model zurückgegeben.
                    Wenn False, wird das generierte Workout als Dictionary (vom Pydantic Schema) zurückgegeben.

    Returns:
        Abhängig von `save_to_db`: das gespeicherte Workout-DB-Modell oder ein Dictionary des generierten Workouts.
    """

    training_principles_text = None
    training_plan_id_for_saving = None
    formatted_history = None

    if user_id is not None:
        # Get training principles from the user's training plan
        training_plan_db_obj = await get_training_plan_for_user(user_id, db)
        if training_plan_db_obj and hasattr(
            training_plan_db_obj, "training_principles"
        ):
            training_principles_text = training_plan_db_obj.training_principles
        if training_plan_db_obj:
            training_plan_id_for_saving = training_plan_db_obj.id
            
            

        # Get and format training history (last 10 workouts)
        raw_training_history: List[Workout] = (
            await get_training_history_for_user_from_db(user_id, db, limit=10)
        )
        
        if raw_training_history:
            formatted_history = format_training_history_for_llm(
                raw_training_history
            )
        
        
        
    # LLM-Call durchführen
    # generate_workout signature will be (training_plan_text, training_history_json, user_prompt)
    llm_output_schema = await generate_workout(
        training_plan=training_principles_text,
        training_history=formatted_history,
        user_prompt=user_prompt,
    )

    workout_model = convert_llm_output_to_db_models(
        llm_output_schema.model_dump(),
        training_plan_id=training_plan_id_for_saving,
    )

    if save_to_db:
        db.add(workout_model)
        await db.commit()
        await db.refresh(workout_model)
        print(
            f"Workout erfolgreich in Datenbank gespeichert mit ID: {workout_model.id}"
        )
        return workout_model
    else:
        # Return the raw Pydantic model output as a dict
        return llm_output_schema.model_dump()

def format_training_history_for_llm(
    training_history_workouts: List[Workout],
) -> str | None:
    """
    Formats the training history into a structured JSON string suitable for the LLM.
    Focuses on when the user trained, their notes, and actual executed exercises.
    Only includes workouts that have at least one completed set.
    Returns None if no workouts are provided.
    """
    if not training_history_workouts:
        return None
    
    # Note: The workout history is already filtered by get_user_workout_history
    # to only include completed sets and their parent elements
    
    history_data = []
    
    for workout in training_history_workouts:
        # Find the earliest completed_at from sets as the workout completion date
        workout_completion_date_str = "N/A"
        earliest_completed_at = None
        
        for block in workout.blocks:
            for exercise in block.exercises:
                for s_set in exercise.sets:
                    if s_set.completed_at:
                        if earliest_completed_at is None or s_set.completed_at < earliest_completed_at:
                            earliest_completed_at = s_set.completed_at
                            
        if earliest_completed_at:
            workout_completion_date_str = earliest_completed_at.strftime("%Y-%m-%d")

        # Create workout object
        workout_obj = {
            "name": workout.name if workout.name else "Unnamed Workout",
            "date": workout_completion_date_str,
            "blocks": []
        }
        
        if workout.focus:
            workout_obj["focus"] = workout.focus
        if workout.duration:
            workout_obj["duration"] = workout.duration
        if workout.notes:
            workout_obj["notes"] = workout.notes
        
        # Add blocks
        for block in workout.blocks:
            block_obj = {
                "name": block.name if block.name else "Unnamed Block",
                "exercises": []
            }
            
            if block.notes:
                block_obj["notes"] = block.notes
            
            # Add exercises
            for exercise in block.exercises:
                exercise_obj = {
                    "name": exercise.name if exercise.name else "Unnamed Exercise",
                    "sets": []
                }
                
                if exercise.notes:
                    exercise_obj["notes"] = exercise.notes
                
                # Add sets
                for s in exercise.sets:
                    set_obj = {}
                    if s.weight is not None:
                        set_obj["weight"] = s.weight
                    if s.reps is not None:
                        set_obj["reps"] = s.reps
                    if s.duration is not None:
                        set_obj["duration"] = s.duration
                    if s.distance is not None:
                        set_obj["distance"] = s.distance
                    if s.rest_time is not None:
                        set_obj["rest"] = s.rest_time
                    
                    if set_obj:  # Only add if there's at least one value
                        exercise_obj["sets"].append(set_obj)
                
                if exercise_obj["sets"]:  # Only add if there's at least one set
                    block_obj["exercises"].append(exercise_obj)
            
            if block_obj["exercises"]:  # Only add if there's at least one exercise
                workout_obj["blocks"].append(block_obj)
        
        if workout_obj["blocks"]:  # Only add if there's at least one block
            history_data.append(workout_obj)

    if not history_data:
        return None

    # Convert to JSON string
    return json.dumps(history_data, ensure_ascii=False)

def convert_llm_output_to_db_models(
    workout_dict: Dict[str, Any],  # Expecting dict from WorkoutSchema.model_dump()
    training_plan_id: Optional[int] = None,
) -> Workout:
    """
    Konvertiert das LLM-Output (Pydantic Schema dict) in ein Workout-DB-Modell
    und zugehörige Block-, Exercise- und Set-Modelle.
    Die 'values' Liste in SetSchema wird in die plan_* Felder des Set-Modells gemappt.
    [weight, reps, duration, distance, rest_time]
    Akzeptiert auch explizite Felder (plan_weight, plan_reps, ...).

    Args:
        workout_dict: Das LLM-Output als Dict (von WorkoutSchema.model_dump()).
        training_plan_id: Optional die ID des Trainingsplans.

    Returns:
        Ein Workout-Modell mit allen Beziehungen.
    """
    # Erstelle das Workout-Modell
    workout_model = Workout(
        training_plan_id=training_plan_id,
        name=workout_dict.get("name", "Unbenanntes Workout"),
        description=workout_dict.get("description"),
        focus=workout_dict.get("focus"),
        duration=workout_dict.get("duration"),
        date_created=datetime.utcnow(),
        blocks=[],
    )

    for block_data in workout_dict.get("blocks", []):
        block_model = Block(
            name=block_data.get("name", "Unbenannter Block"),
            description=block_data.get("description"),
            exercises=[],
        )

        for exercise_data in block_data.get("exercises", []):
            exercise_model = Exercise(
                name=exercise_data.get("name", "Unbenannte Übung"),
                description=exercise_data.get("description"),
                sets=[],
            )

            for set_data_from_llm in exercise_data.get("sets", []):
                set_obj = None
                if isinstance(set_data_from_llm, dict) and "values" in set_data_from_llm:
                    values = set_data_from_llm.get("values", [])
                    if not isinstance(values, list):
                        print(f"Skipping set data as 'values' is not a list: {values}")
                        continue

                    # Ensure values list has at least 5 elements, padding with None if shorter
                    padded_values = (values + [None] * 5)[:5]
                    
                    v_weight, v_reps, v_duration, v_distance, v_rest_time = padded_values

                    # Check if any numerical value is present or if notes are present
                    has_numerical_value = any(
                        val is not None for val in [v_weight, v_reps, v_duration, v_distance, v_rest_time]
                    )

                    if has_numerical_value:
                        set_obj = Set(
                            weight=float(v_weight) if v_weight is not None else None,
                            reps=int(v_reps) if v_reps is not None else None,
                            duration=int(v_duration) if v_duration is not None else None,
                            distance=float(v_distance) if v_distance is not None else None,
                            rest_time=int(v_rest_time) if v_rest_time is not None else None,
                        )
                    else:
                        print(f"Skipping set data as all values are None and no notes provided: {values}")
                        continue
                else:
                    print(f"Skipping set data due to unexpected format or missing 'values' key: {set_data_from_llm}")
                    continue
                
                if set_obj:
                    exercise_model.sets.append(set_obj)

            if exercise_model.sets:
                block_model.exercises.append(exercise_model)

        if block_model.exercises:
            workout_model.blocks.append(block_model)

    return workout_model
