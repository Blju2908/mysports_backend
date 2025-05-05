from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.workout_model import Workout
from app.models.block_model import Block, BlockStatus
from app.models.exercise_model import Exercise 
from app.schemas.workout_schema import WorkoutSchemaWithBlocks
from app.models.set_model import Set
from datetime import datetime

async def get_workout_details(
    *, 
    workout_id: int, 
    db: AsyncSession
) -> Workout:
    """Retrieves detailed workout information for a specific workout ID.

    Includes blocks, exercises, and sets.

    Args:
        workout_id: The ID of the workout to retrieve.
        db: The asynchronous database session.

    Returns:
        The Workout object with eagerly loaded details.

    Raises:
        HTTPException(status_code=404): If the workout is not found.
    """
    # 1. Get the specific workout, eagerly loading blocks -> exercises -> sets
    workout_query = select(Workout).options(
        selectinload(Workout.blocks).selectinload(Block.exercises).selectinload(Exercise.sets)
    ).where(
        Workout.id == workout_id
    )
    result = await db.execute(workout_query)
    workout: Workout | None = result.scalar_one_or_none()

    if not workout:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workout not found"
        )

    # 2. Explicitly sort blocks after loading (important for consistent frontend display)
    if workout.blocks:
        workout.blocks.sort(key=lambda block: block.id if block.id is not None else 0)

    return workout 

async def save_workout_to_db_async(
    *,
    workout_schema: WorkoutSchemaWithBlocks,
    training_plan_id: int,
    db: AsyncSession
) -> Workout:
    """
    Speichert das generierte Workout in der Datenbank und gibt das gespeicherte Workout-Objekt zurück.
    """
    workout_db = Workout(
        training_plan_id=training_plan_id,
        name=workout_schema.name,
        date=datetime.now(),
        description=workout_schema.description,
    )
    db.add(workout_db)
    await db.flush()
    await db.refresh(workout_db)

    if workout_schema.blocks:
        for block_schema in workout_schema.blocks:
            block_db = Block(
                workout_id=workout_db.id,
                name=block_schema.name,
                description=block_schema.description,
                status=BlockStatus.open
            )
            db.add(block_db)
            await db.flush()
            await db.refresh(block_db)

            if block_schema.exercises:
                for exercise_schema in block_schema.exercises:
                    exercise_db = Exercise(
                        block_id=block_db.id,
                        name=exercise_schema.name,
                        description=exercise_schema.description
                    )
                    db.add(exercise_db)
                    await db.flush()
                    await db.refresh(exercise_db)

                    if exercise_schema.sets:
                        for set_schema in exercise_schema.sets:
                            set_db = Set(
                                exercise_id=exercise_db.id,
                                weight=set_schema.weight,
                                reps=set_schema.reps,
                                duration=set_schema.duration,
                                distance=set_schema.distance,
                                speed=set_schema.speed,
                                rest_time=set_schema.rest_time
                            )
                            db.add(set_db)
    await db.commit()
    await db.refresh(workout_db)
    return workout_db 