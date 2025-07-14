from typing import List, Optional
from uuid import UUID
from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from sqlmodel.ext.asyncio.session import AsyncSession


def parse_compact_workout_to_db_models(
    compact_workout: CompactWorkoutSchema,
    user_id: UUID,
    training_plan_id: Optional[int],
) -> Workout:
    """
    Translates a CompactWorkoutSchema object into a tree of SQLModel objects
    (Workout, Block, Exercise, Set) ready for database insertion.
    """

    workout_obj = Workout(
        user_id=user_id,
        training_plan_id=training_plan_id,
        name=compact_workout.name,
        description=compact_workout.description,
        duration=compact_workout.duration_min,
        focus=compact_workout.focus,
        notes=f"Focus derivation: {compact_workout.focus_derivation}\n\nMuscle group load: {'; '.join(compact_workout.muscle_group_load)}",
        blocks=[],
    )

    for block_pos, compact_block in enumerate(compact_workout.blocks):
        block_obj = Block(
            name=compact_block.name,
            description=compact_block.description,
            position=block_pos,
            exercises=[],
        )

        for exercise_pos, compact_exercise in enumerate(compact_block.exercises):
            exercise_obj = Exercise(
                name=compact_exercise.name,
                superset_id=compact_exercise.superset_group,
                position=exercise_pos,
                sets=[],
            )

            for set_pos, compact_set in enumerate(compact_exercise.sets):
                # Map from CompactSetSchema to Set
                set_obj = Set(
                    reps=compact_set.r,
                    weight=compact_set.w,
                    duration=compact_set.s,
                    distance=compact_set.d,
                    rest_time=compact_set.p,
                    position=set_pos,
                    status=SetStatus.open,
                )
                # Only add set if it has any values to avoid empty sets
                if any(
                    v is not None
                    for v in [
                        compact_set.r,
                        compact_set.w,
                        compact_set.s,
                        compact_set.d,
                        compact_set.p,
                    ]
                ):
                    exercise_obj.sets.append(set_obj)

            if exercise_obj.sets:
                block_obj.exercises.append(exercise_obj)

        if block_obj.exercises:
            workout_obj.blocks.append(block_obj)

    return workout_obj


def update_existing_workout_with_compact_data(
    existing_workout: Workout,
    compact_workout: CompactWorkoutSchema,
    training_plan_id: Optional[int] = None,
) -> None:
    """
    ✅ FIX: Updates an existing workout object with data from CompactWorkoutSchema.
    This avoids creating duplicate workouts by working directly with the existing object.
    
    Args:
        existing_workout: The existing workout object to update
        compact_workout: The compact workout data from the LLM
        training_plan_id: Optional training plan ID to set
    """
    # Update basic workout fields
    existing_workout.name = compact_workout.name
    existing_workout.description = compact_workout.description
    existing_workout.duration = compact_workout.duration_min
    existing_workout.focus = compact_workout.focus
    existing_workout.notes = f"Focus derivation: {compact_workout.focus_derivation}\n\nMuscle group load: {'; '.join(compact_workout.muscle_group_load)}"
    
    if training_plan_id is not None:
        existing_workout.training_plan_id = training_plan_id
    
    # Clear existing blocks properly by clearing the list in-place
    # This triggers SQLAlchemy to delete the old blocks
    existing_workout.blocks.clear()
    
    # Create new blocks from compact data
    for block_pos, compact_block in enumerate(compact_workout.blocks):
        block_obj = Block(
            name=compact_block.name,
            description=compact_block.description,
            position=block_pos,
            exercises=[],
        )

        for exercise_pos, compact_exercise in enumerate(compact_block.exercises):
            exercise_obj = Exercise(
                name=compact_exercise.name,
                superset_id=compact_exercise.superset_group,
                position=exercise_pos,
                sets=[],
            )

            for set_pos, compact_set in enumerate(compact_exercise.sets):
                # Map from CompactSetSchema to Set
                set_obj = Set(
                    reps=compact_set.r,
                    weight=compact_set.w,
                    duration=compact_set.s,
                    distance=compact_set.d,
                    rest_time=compact_set.p,
                    position=set_pos,
                    status=SetStatus.open,
                )
                # Only add set if it has any values to avoid empty sets
                if any(
                    v is not None
                    for v in [
                        compact_set.r,
                        compact_set.w,
                        compact_set.s,
                        compact_set.d,
                        compact_set.p,
                    ]
                ):
                    exercise_obj.sets.append(set_obj)

            if exercise_obj.sets:
                block_obj.exercises.append(exercise_obj)

        if block_obj.exercises:
            existing_workout.blocks.append(block_obj)


def update_existing_workout_with_revision_data(
    existing_workout: Workout,
    revision_data: dict,
) -> None:
    """
    ✅ FIX: Updates an existing workout object with revision data from frontend preview format.
    This avoids creating duplicate workouts in the revision acceptance flow.
    
    Args:
        existing_workout: The existing workout object to update
        revision_data: The revision data dictionary (from frontend preview format)
    """
    # Update basic workout fields
    existing_workout.name = revision_data.get("name", existing_workout.name)
    existing_workout.description = revision_data.get("description", existing_workout.description)
    existing_workout.duration = revision_data.get("duration", existing_workout.duration)
    existing_workout.focus = revision_data.get("focus", existing_workout.focus)
    existing_workout.notes = revision_data.get("notes", existing_workout.notes)
    
    # ✅ FIX: Blocks are already deleted in the endpoint
    # Just clear the list to ensure it's empty
    existing_workout.blocks = []
    
    # Create new blocks from revision data
    blocks_data = revision_data.get("blocks", [])
    for block_data in blocks_data:
        block_obj = Block(
            name=block_data.get("name", ""),
            description=block_data.get("description", ""),
            position=block_data.get("position", 0),
            exercises=[],
        )

        exercises_data = block_data.get("exercises", [])
        for exercise_data in exercises_data:
            exercise_obj = Exercise(
                name=exercise_data.get("name", ""),
                superset_id=exercise_data.get("superset_id"),
                position=exercise_data.get("position", 0),
                sets=[],
            )

            sets_data = exercise_data.get("sets", [])
            for set_pos, set_data in enumerate(sets_data):
                # Extract values from the "values" array [reps, weight, duration, distance, rest_time]
                values = set_data.get("values", [None, None, None, None, None])
                
                set_obj = Set(
                    reps=values[0] if len(values) > 0 else None,
                    weight=values[1] if len(values) > 1 else None,
                    duration=values[2] if len(values) > 2 else None,
                    distance=values[3] if len(values) > 3 else None,
                    rest_time=values[4] if len(values) > 4 else None,
                    position=set_data.get("position", set_pos),
                    status=SetStatus.open,
                )
                
                # Only add set if it has any values to avoid empty sets
                if any(v is not None for v in values):
                    exercise_obj.sets.append(set_obj)

            if exercise_obj.sets:
                block_obj.exercises.append(exercise_obj)

        if block_obj.exercises:
            existing_workout.blocks.append(block_obj) 