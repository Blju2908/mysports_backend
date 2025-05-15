from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List, Dict, Optional

from app.db.trainingplan_db_access import get_training_plan_for_user
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.chains.workout_generation_chain import generate_workout
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from datetime import datetime
import json
from pathlib import Path

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
    formatted_history_json = None

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
            formatted_history_json = format_training_history_for_llm(
                raw_training_history
            )

    # LLM-Call durchführen
    # generate_workout signature will be (training_plan_text, training_history_json, user_prompt)
    llm_output_schema = await generate_workout(
        training_plan=training_principles_text,
        training_history=formatted_history_json,
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
    Formats the training history into a compact plain text string suitable for the LLM.
    Focuses on when the user trained, their notes, and actual executed exercises.
    Set parameters are comma-separated: weight, reps, duration, distance, rest_time.
    Only includes sets with status 'done'.
    """
    if not training_history_workouts:
        return None

    history_lines = []
    for workout_idx, workout in enumerate(training_history_workouts):
        if workout_idx > 0:
            history_lines.append("---") # Separator for multiple workouts

        # Get the earliest completed_at from sets as the workout completion date
        workout_completion_date_str = "N/A"
        earliest_completed_at = None
        if workout.blocks:
            for block in workout.blocks:
                if block.exercises:
                    for exercise in block.exercises:
                        if exercise.sets:
                            for s_set in exercise.sets:
                                if s_set.status == SetStatus.done and s_set.completed_at:
                                    if earliest_completed_at is None or s_set.completed_at < earliest_completed_at:
                                        earliest_completed_at = s_set.completed_at
        if earliest_completed_at:
            workout_completion_date_str = earliest_completed_at.strftime("%Y-%m-%d")

        history_lines.append(f"Workout: {workout.name if workout.name else 'Unnamed Workout'}")
        if workout.focus:
            history_lines.append(f"Focus: {workout.focus}")
        if workout.duration:
            history_lines.append(f"Duration: {workout.duration} min")
        history_lines.append(f"Date: {workout_completion_date_str}")
        if workout.notes:
            history_lines.append(f"Workout Notes: {workout.notes}")
        
        history_lines.append("") # Add a blank line for readability

        for block in workout.blocks:
            history_lines.append(f"  Block: {block.name if block.name else 'Unnamed Block'}")
            if block.notes:
                history_lines.append(f"  Block Notes: {block.notes}")
            
            for exercise in block.exercises:
                history_lines.append(f"    Exercise: {exercise.name if exercise.name else 'Unnamed Exercise'}")
                if exercise.notes:
                    history_lines.append(f"    Exercise Notes: {exercise.notes}")
                
                executed_sets_lines = []
                for s in exercise.sets:
                    if s.status == SetStatus.done:  # Only include completed sets
                        # weight, reps, duration, distance, rest_time
                        set_params_list = [
                            str(s.weight if s.weight is not None else "null"),
                            str(s.reps if s.reps is not None else "null"),
                            str(s.duration if s.duration is not None else "null"),
                            str(s.distance if s.distance is not None else "null"),
                            str(s.rest_time if s.rest_time is not None else "null"),
                        ]
                        executed_sets_lines.append(f"      - {', '.join(set_params_list)}")

                if executed_sets_lines:
                    history_lines.append("    Sets completed:")
                    history_lines.extend(executed_sets_lines)
            history_lines.append("") # Add a blank line after each exercise block for readability
        history_lines.append("") # Add a blank line after each workout block for readability


    if not history_lines:
        return None

    history_text_output = "\\n".join(history_lines)

    # Save to file for debugging (optional, can be removed in production)
    output_dir = Path(__file__).resolve().parents[1] / "local_execution" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"formatted_training_history_text_{timestamp}.txt"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(history_text_output.replace("\\\\n", "\\n")) # For readability in the text file
    print(f"Formatted text training history saved to: {file_path}")

    return history_text_output




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
