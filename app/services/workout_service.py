from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload, contains_eager, aliased
from typing import List

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from uuid import UUID


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


async def get_latest_workouts_with_details(
    *, 
    db: AsyncSession,
    user_id: UUID,
    number_of_workouts: int = 10
) -> List[Workout]:
    """Retrieves the most recent workouts with all their associated blocks, exercises, and sets for a given user.

    Args:
        db: The asynchronous database session.
        user_id: The UUID of the user.
        number_of_workouts: The number of latest workouts to retrieve. Defaults to 10.

    Returns:
        A list of the most recent Workout objects for the user with eagerly loaded details.
    """
    workouts_query = select(Workout).options(
        selectinload(Workout.blocks).selectinload(Block.exercises).selectinload(Exercise.sets)
    ).where(Workout.user_id == user_id).order_by(Workout.date_created.desc()).limit(number_of_workouts)
    
    result = await db.execute(workouts_query)
    workouts: List[Workout] = result.scalars().unique().all()

    return workouts


async def get_exercises_with_done_sets_only(
    db: AsyncSession,
    current_user_id: UUID,
    number_of_workouts: int = 10
) -> List[Exercise]:
    """
    Retrieves exercises that contain at least one 'done' set for a specific user,
    and for each exercise, only includes 'done' sets in its relationship.
    """
    set_alias = aliased(Set)

    query = (
        select(Exercise)
        .join(set_alias, Exercise.sets)
        .join(Exercise.block) 
        .join(Block.workout)  
        .where(
            set_alias.status == SetStatus.done,
            Workout.user_id == current_user_id
        )
        .options(
            contains_eager(Exercise.sets, alias=set_alias),
            contains_eager(Exercise.block)
        )
        .order_by(Exercise.id)
        .limit(number_of_workouts)
    )

    result = await db.execute(query)
    exercises: List[Exercise] = result.scalars().unique().all()
    return exercises


