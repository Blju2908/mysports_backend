from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List, Dict, Optional

from app.db.trainingplan_db_access import get_training_plan_for_user
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.chains.workout_generation_chain import generate_workout
from app.services.workout_service import save_workout_to_db_async
from app.llm.schemas.create_workout_schemas import (
    WorkoutSchema,
    BlockSchema,
    ExerciseSchema,
    SetSchema,
)
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from datetime import datetime
from collections import defaultdict, OrderedDict
import json
from pathlib import Path
import pickle

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
        llm_output_schema.model_dump(),  # Pass the dict from Pydantic model
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
    Formats the training history into a compact JSON string suitable for the LLM.
    Focuses on when the user trained, their notes, and actual executed exercises.
    Set parameters are standardized: [weight, reps, duration, distance, rest_time].
    Only includes sets with status 'done'.
    """
    if not training_history_workouts:
        return None

    history_output_condensed = []
    for workout in training_history_workouts:
        workout_data = {
            "workout_notes": workout.notes if workout.notes else None,
            "date": (
                next(
                    (
                        s.completed_at.strftime("%Y-%m-%d")
                        for block in workout.blocks or []
                        for exercise in block.exercises or []
                        for s in exercise.sets or []
                        if s.completed_at
                    ),
                    None,
                )
            ),
            "blocks": [],
        }
        for block in workout.blocks:
            block_data = {
                "block_notes": block.notes if block.notes else None,
                "exercises_executed": [],  # Focus on executed exercises
            }
            for exercise in block.exercises:
                executed_sets_data = []
                for s in exercise.sets:
                    if s.status == SetStatus.done:  # Only include completed sets
                        # Standardized array: [weight, reps, duration, distance, rest_time]
                        # Fill with 0.0 or 0 if None, to maintain array structure for LLM
                        set_params = [
                            (
                                s.execution_weight
                                if s.execution_weight is not None
                                else 0.0
                            ),
                            s.execution_reps if s.execution_reps is not None else 0,
                            (
                                s.execution_duration
                                if s.execution_duration is not None
                                else 0
                            ),  # seconds
                            (
                                s.execution_distance
                                if s.execution_distance is not None
                                else 0.0
                            ),
                            s.rest_time if s.rest_time is not None else 0,  # seconds
                        ]
                        set_info = {
                            "params": set_params,
                            "set_notes": s.notes if s.notes else None,
                        }
                        executed_sets_data.append(set_info)

                if executed_sets_data:  # Only add exercises that have completed sets
                    exercise_info = {
                        "name": exercise.name,
                        "exercise_notes": exercise.notes if exercise.notes else None,
                        "sets_completed": executed_sets_data,
                    }
                    block_data["exercises_executed"].append(exercise_info)

            if block_data[
                "exercises_executed"
            ]:  # Only add blocks that have executed exercises
                workout_data["blocks"].append(block_data)

        if workout_data["blocks"]:  # Only add workouts that have executed blocks
            history_output_condensed.append(workout_data)

    if not history_output_condensed:
        return None

    history_json_str = json.dumps(
        history_output_condensed, indent=2, ensure_ascii=False
    )

    # Save to file for debugging (optional, can be removed in production)
    output_dir = Path(__file__).resolve().parents[1] / "local_execution" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = output_dir / f"formatted_training_history_condensed_{timestamp}.json"
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(history_json_str)
    print(f"Formatted condensed training history saved to: {file_path}")

    return history_json_str




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
        notes=workout_dict.get("notes"),
        focus=workout_dict.get("focus"),
        duration=workout_dict.get("duration"),
        blocks=[],
    )

    for block_data in workout_dict.get("blocks", []):
        block_model = Block(
            name=block_data.get("name", "Unbenannter Block"),
            description=block_data.get("description"),
            notes=block_data.get("notes"),
            exercises=[],
        )

        for exercise_data in block_data.get("exercises", []):
            exercise_model = Exercise(
                name=exercise_data.get("name", "Unbenannte Übung"),
                description=exercise_data.get("description"),
                notes=exercise_data.get("notes"),
                sets=[],
            )

            for set_data_from_llm in exercise_data.get("sets", []):
                # Accept both explicit field format and old 'values' array format
                if isinstance(set_data_from_llm, dict):
                    # Prefer explicit fields if present
                    if any(
                        k in set_data_from_llm
                        for k in [
                            "plan_weight",
                            "plan_reps",
                            "plan_duration",
                            "plan_distance",
                            "rest_time",
                        ]
                    ):
                        set_obj = Set(
                            plan_weight=(
                                float(set_data_from_llm.get("plan_weight"))
                                if set_data_from_llm.get("plan_weight") is not None
                                else None
                            ),
                            plan_reps=(
                                int(set_data_from_llm.get("plan_reps"))
                                if set_data_from_llm.get("plan_reps") is not None
                                else None
                            ),
                            plan_duration=(
                                int(set_data_from_llm.get("plan_duration"))
                                if set_data_from_llm.get("plan_duration") is not None
                                else None
                            ),
                            plan_distance=(
                                float(set_data_from_llm.get("plan_distance"))
                                if set_data_from_llm.get("plan_distance") is not None
                                else None
                            ),
                            rest_time=(
                                int(set_data_from_llm.get("rest_time"))
                                if set_data_from_llm.get("rest_time") is not None
                                else None
                            ),
                            notes=set_data_from_llm.get("notes"),
                        )
                    elif "values" in set_data_from_llm:
                        values = set_data_from_llm.get("values", [])
                        set_notes = set_data_from_llm.get("notes")
                        # [weight, reps, duration, distance, rest_time]
                        (
                            plan_weight,
                            plan_reps,
                            plan_duration,
                            plan_distance,
                            rest_time_val,
                        ) = (values + [None] * 5)[:5]
                        set_obj = Set(
                            plan_weight=(
                                float(plan_weight) if plan_weight is not None else None
                            ),
                            plan_reps=int(plan_reps) if plan_reps is not None else None,
                            plan_duration=(
                                int(plan_duration)
                                if plan_duration is not None
                                else None
                            ),
                            plan_distance=(
                                float(plan_distance)
                                if plan_distance is not None
                                else None
                            ),
                            rest_time=(
                                int(rest_time_val)
                                if rest_time_val is not None
                                else None
                            ),
                            notes=set_notes,
                        )
                    else:
                        print(
                            f"Skipping set data due to unexpected format: {set_data_from_llm}"
                        )
                        continue
                else:
                    print(
                        f"Skipping set data due to unexpected type: {set_data_from_llm}"
                    )
                    continue

                if any(
                    [
                        set_obj.plan_weight is not None,
                        set_obj.plan_reps is not None,
                        set_obj.plan_duration is not None,
                        set_obj.plan_distance is not None,
                        set_obj.rest_time is not None,
                        set_obj.notes is not None,
                    ]
                ):
                    exercise_model.sets.append(set_obj)

            if exercise_model.sets:
                block_model.exercises.append(exercise_model)

        if block_model.exercises:
            workout_model.blocks.append(block_model)

    return workout_model
