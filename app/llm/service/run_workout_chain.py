from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List

from app.db.trainingplan_db_access import get_training_plan_for_user
from app.db.training_history import get_training_history_for_user
from app.llm.chains.workout_generation_chain import generate_workout
from app.services.workout_service import save_workout_to_db_async
from app.llm.schemas.workout_generation_schema import (
    WorkoutSchema,
    BlockSchema,
    ExerciseSchema,
    SetSchema,
)
from app.models.workout_model import Workout
from app.models.block_model import Block, BlockStatus
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from datetime import datetime
from collections import defaultdict, OrderedDict
import json
import pickle


async def run_workout_chain(
    user_id: UUID | None, 
    user_prompt: str | None, 
    db: AsyncSession, 
    save_to_db: bool = False
) -> Any:
    """
    Führt den Workout-Generierungs-Prozess mit dem LLM durch.

    Args:
        user_id: Die ID des Benutzers
        user_prompt: Ein optionaler Prompt des Benutzers
        db: Die Datenbankverbindung
        save_to_db: Ob das Workout in der Datenbank gespeichert werden soll

    Returns:
        Das generierte Workout-Objekt oder das gespeicherte Workout
    """
    if user_id is not None:
        training_plan = await get_training_plan_for_user(user_id, db)
        training_history = await get_training_history_for_user(user_id, db)
        filtered_training_history = filter_training_history(training_history)
    else:
        filtered_training_history = None
        training_plan = None

    # LLM-Call durchführen
    result = await generate_workout(
        training_plan, filtered_training_history, user_prompt
    )

    # Konvertiere das LLM-Ergebnis in ein Datenbankmodell
    workout_model = convert_llm_output_to_db_models(
        result.model_dump(),
        training_plan_id=training_plan.id if training_plan else None,
    )

    # Optional: Speichere das Workout in der Datenbank
    if save_to_db:
        # Datenbank speichern
        db.add(workout_model)
        await db.commit()
        await db.refresh(workout_model)
        print(
            f"Workout erfolgreich in Datenbank gespeichert mit ID: {workout_model.id}"
        )
        return workout_model
    else:
        return workout_model


def convert_llm_output_to_db_models(
    workout_dict: dict, training_plan_id: int = None
) -> Workout:
    """
    Konvertiert das LLM-Output (workout_short.json) direkt in ein Workout-Modell und
    zugehörige Block-, Exercise- und Set-Modelle für die Datenbank.

    Args:
        workout_dict: Das LLM-Output als Dict
        training_plan_id: Optional die ID des Trainingsplans

    Returns:
        Ein Workout-Modell mit allen Beziehungen
    """
    # Erstelle das Workout-Modell
    workout = Workout(
        training_plan_id=training_plan_id or workout_dict.get("training_plan_id"),
        name=workout_dict.get("name", "Unbenanntes Workout"),
        description=workout_dict.get("description", ""),
        date=datetime.now(),
        blocks=[],  # Wird später befüllt
    )

    # Erstelle für jeden Block im Workout ein Block-Modell
    for block_data in workout_dict.get("blocks", []):
        block = Block(
            name=block_data.get("name", ""),
            description=block_data.get("description", ""),
            status=BlockStatus.open,
            exercises=[],  # Wird später befüllt
        )

        # Erstelle für jede Übung im Block ein Exercise-Modell
        for exercise_data in block_data.get("exercises", []):
            exercise = Exercise(
                name=exercise_data.get("name", ""),
                description=exercise_data.get("description", ""),
                sets=[],  # Wird später befüllt
            )

            # Erstelle für jeden Satz in der Übung ein Set-Modell
            for set_data in exercise_data.get("sets", []):
                # Extrahiere die Values aus dem Set
                values = []
                if isinstance(set_data, dict) and "values" in set_data:
                    # Neues Format: {"values": [weight, reps, duration, distance, speed, rest_time]}
                    values = set_data["values"]
                elif isinstance(set_data, list):
                    # Älteres Format: [weight, reps, duration, distance, speed, rest_time]
                    values = set_data

                # Stelle sicher, dass values eine Liste ist und vollständig
                if not isinstance(values, list):
                    values = [values]

                while len(values) < 6:
                    values.append(None)

                # Erstelle das Set-Modell mit den extrahierten Werten
                set_obj = Set(
                    weight=values[0] if values[0] not in (None, 0, 0.0) else None,
                    reps=int(values[1]) if values[1] not in (None, 0, 0.0) else None,
                    duration=(
                        int(values[2]) if values[2] not in (None, 0, 0.0) else None
                    ),
                    distance=values[3] if values[3] not in (None, 0, 0.0) else None,
                    speed=values[4] if values[4] not in (None, 0, 0.0) else None,
                    rest_time=(
                        int(values[5]) if values[5] not in (None, 0, 0.0) else None
                    ),
                )

                # Füge das Set der Übung hinzu
                exercise.sets.append(set_obj)

            # Nur Übungen mit mindestens einem Set hinzufügen
            if exercise.sets:
                block.exercises.append(exercise)

        # Nur Blöcke mit mindestens einer Übung hinzufügen
        if block.exercises:
            workout.blocks.append(block)

    return workout


def filter_training_history(training_history: list) -> str:
    """
    Gibt die Trainingshistorie als kompakten Klartext zurück, gruppiert nach Datum und Übung.
    Die Übungen pro Tag werden in der Reihenfolge ihres ersten Auftretens (timestamp) gelistet.
    Beispiel:
    2025-05-04
    Kettlebell Swings:
      24kg, 20 reps
      24kg, 20 reps
    Klimmzüge (Band):
      6 reps
    """
    set_fields = ["weight", "reps", "duration"]
    # Gruppierung: {datum: OrderedDict{übung: [satzdict, ...]}}
    grouped = defaultdict(lambda: OrderedDict())
    # Hilfsstruktur, um die Reihenfolge der Übungen nach erstem Auftreten zu sichern
    for entry in sorted(
        training_history, key=lambda e: (str(e.timestamp)[:10], e.timestamp)
    ):
        entry_dict = entry.model_dump() if hasattr(entry, "model_dump") else dict(entry)
        # Datum normalisieren
        ts = entry_dict.get("timestamp")
        try:
            dt = datetime.fromisoformat(str(ts))
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = str(ts)[:10]
        exercise = entry_dict.get("exercise_name")
        set_data = {
            k: v for k, v in entry_dict.items() if k in set_fields and v is not None
        }
        # Reihenfolge der Übungen nach erstem Auftreten sichern
        if exercise not in grouped[date_str]:
            grouped[date_str][exercise] = []
        grouped[date_str][exercise].append(set_data)

    # Text bauen
    lines = []
    for date in sorted(grouped.keys(), reverse=True):
        lines.append(date)
        for exercise, sets in grouped[date].items():
            lines.append(f"{exercise}:")
            for set_data in sets:
                attribs = []
                if "weight" in set_data:
                    attribs.append(f"{set_data['weight']}kg")
                if "reps" in set_data:
                    attribs.append(f"{set_data['reps']} reps")
                if "duration" in set_data:
                    attribs.append(f"{set_data['duration']} sek")
                attrib_str = ", ".join(attribs)
                lines.append(f"  {attrib_str}" if attrib_str else "  -")
    return "\n".join(lines)
