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


async def save_workout_to_db(workout: Workout, db_session: AsyncSession) -> Workout:
    """
    Saves the complete Workout object tree to the database.
    """
    db_session.add(workout)
    await db_session.commit()
    await db_session.refresh(workout)

    return workout 