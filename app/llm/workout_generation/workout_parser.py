import re
from typing import Tuple

from app.llm.workout_generation.create_workout_schemas import (
    BlockSchema,
    CompactWorkoutSchema,
    ExerciseSchema,
    SetSchema,
    WorkoutSchema,
)


def _parse_set_string(set_str: str) -> SetSchema:
    """
    Parses a formatted string (e.g., '10r / 20kg / P: 60s') into a SetSchema object.
    This function uses a robust method of splitting the string and parsing each part
    to handle various combinations of parameters like reps, weight, distance, duration, and rest.
    """
    parts = [p.strip() for p in set_str.split("/")]
    params = {}
    for part in parts:
        # Match repetitions (e.g., '8r', '12r')
        if "r" in part and "kg" not in part:
            match = re.match(r"(\d+)", part)
            if match:
                params["reps"] = int(match.group(1))
        # Match weight (e.g., '80kg', '22.5kg')
        elif "kg" in part:
            match = re.match(r"(\d+(?:\.\d+)?)", part)
            if match:
                params["weight"] = float(match.group(1))
        # Match distance (e.g., '300m')
        elif "m" in part:
            match = re.match(r"(\d+(?:\.\d+)?)", part)
            if match:
                params["distance"] = float(match.group(1))
        # Match rest period (e.g., 'P: 60s', 'P:120s')
        elif "P:" in part:
            match = re.search(r"(\d+)", part)
            if match:
                params["rest_seconds"] = int(match.group(1))
        # Match duration (e.g., '60s')
        elif "s" in part:
            match = re.match(r"(\d+)", part)
            if match:
                params["duration_seconds"] = int(match.group(1))

    # Ensure all fields exist, defaulting to None if not found
    return SetSchema(
        reps=params.get("reps"),
        weight=params.get("weight"),
        distance=params.get("distance"),
        duration_seconds=params.get("duration_seconds"),
        rest_seconds=params.get("rest_seconds"),
    )


def _parse_workout_header(header: str) -> Tuple[str, int, str, str]:
    """
    Parses the workout header string to extract the name, duration, focus, and description.
    Example: 'Intensives Oberkörper-Workout (≈60 min | Fokus: Kraft, Muskelaufbau | Description: Ein anspruchsvolles...)'
    """
    name_match = re.match(r"([^()]+)", header)
    name = name_match.group(1).strip() if name_match else "Workout"

    duration_match = re.search(r"(\d+)\s*min", header)
    duration = int(duration_match.group(1)) if duration_match else 0

    focus_match = re.search(r"Fokus:\s*([^|)]+)", header, re.IGNORECASE)
    focus = focus_match.group(1).strip() if focus_match else ""

    desc_match = re.search(r"Description:\s*([^)]+)", header, re.IGNORECASE)
    description = desc_match.group(1).strip() if desc_match else ""

    return name, duration, focus, description


def _parse_block_header(header: str) -> Tuple[str, str]:
    """
    Parses the block header string to extract the block's name and description.
    Example: 'Main | 50 min | Hauptteil mit Fokus auf Push & Pull'
    """
    parts = [p.strip() for p in header.split("|")]
    name = parts[0]
    # The description is assumed to be the last part if there are multiple parts.
    description = parts[-1] if len(parts) > 1 else ""
    return name, description


def convert_compact_to_verbose_schema(
    compact_workout: CompactWorkoutSchema,
) -> WorkoutSchema:
    """
    Converts a CompactWorkoutSchema, which is optimized for LLM generation,
    into the application's more structured and verbose WorkoutSchema.
    """
    name, duration, focus, description = _parse_workout_header(compact_workout.header)

    verbose_blocks = []
    for i, compact_block in enumerate(compact_workout.blocks):
        block_name, block_desc = _parse_block_header(compact_block.header)

        verbose_exercises = []
        for j, compact_exercise in enumerate(compact_block.exercises):
            verbose_sets = [_parse_set_string(s) for s in compact_exercise.sets]

            verbose_exercise = ExerciseSchema(
                name=compact_exercise.name,
                sets=verbose_sets,
                superset_group=compact_exercise.superset_group,
                position=j,
            )
            verbose_exercises.append(verbose_exercise)

        verbose_block = BlockSchema(
            name=block_name,
            description=block_desc,
            exercises=verbose_exercises,
            position=i,
        )
        verbose_blocks.append(verbose_block)

    return WorkoutSchema(
        name=name,
        description=description,
        duration=duration,
        focus=focus,
        blocks=verbose_blocks,
    ) 