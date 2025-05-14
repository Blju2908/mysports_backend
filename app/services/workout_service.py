from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise 
from app.schemas.workout_schema import WorkoutSchemaWithBlocks, BlockResponseSchema, ExerciseResponseSchema, SetResponseSchema
from app.models.set_model import Set, SetStatus
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
    Verwendet jetzt auch focus, duration und notes vom workout_schema.
    """
    workout_db = Workout(
        training_plan_id=training_plan_id,
        name=workout_schema.name,
        date_created=datetime.utcnow(),  # Set creation date
        description=workout_schema.description,
        notes=workout_schema.notes, # Use notes from schema
        focus=workout_schema.focus, # Use focus from schema
        duration=workout_schema.duration # Use duration from schema
    )
    db.add(workout_db)
    await db.flush() # Flush to get workout_db.id
    # await db.refresh(workout_db) # Refresh later after all children are added or before returning

    if workout_schema.blocks:
        for block_schema in workout_schema.blocks: # block_schema is BlockResponseSchema
            block_db = Block(
                workout_id=workout_db.id, # Ensure workout_db.id is available
                name=block_schema.name,
                description=block_schema.description,
                notes=block_schema.notes  # Use notes from block_schema
            )
            db.add(block_db)
            await db.flush() # Flush to get block_db.id
            # await db.refresh(block_db)

            if block_schema.exercises:
                for exercise_schema in block_schema.exercises: # exercise_schema is ExerciseResponseSchema
                    exercise_db = Exercise(
                        block_id=block_db.id, # Ensure block_db.id is available
                        name=exercise_schema.name,
                        description=exercise_schema.description,
                        notes=exercise_schema.notes  # Use notes from exercise_schema
                    )
                    db.add(exercise_db)
                    await db.flush() # Flush to get exercise_db.id
                    # await db.refresh(exercise_db)

                    if exercise_schema.sets:
                        for set_schema in exercise_schema.sets: # set_schema is SetResponseSchema
                            set_db = Set(
                                exercise_id=exercise_db.id, # Ensure exercise_db.id is available
                                plan_weight=set_schema.plan_weight, # SetResponseSchema now has plan_*
                                plan_reps=set_schema.plan_reps,
                                plan_duration=set_schema.plan_duration,
                                plan_distance=set_schema.plan_distance,
                                execution_weight=set_schema.execution_weight, # Can also set execution if provided
                                execution_reps=set_schema.execution_reps,
                                execution_duration=set_schema.execution_duration,
                                execution_distance=set_schema.execution_distance,
                                rest_time=set_schema.rest_time,
                                notes=set_schema.notes,
                                status=set_schema.status if set_schema.status else SetStatus.open,
                                completed_at=set_schema.completed_at
                            )
                            db.add(set_db)
    
    await db.commit() # Single commit at the end
    await db.refresh(workout_db) # Refresh the main workout object to get all relationships populated
    # Need to refresh children too if they are accessed immediately after and need their own children loaded
    # However, typically the ORM handles relationship loading based on schema access.
    return workout_db 