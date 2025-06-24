from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise


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

    return workout 