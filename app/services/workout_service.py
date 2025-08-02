from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload, contains_eager, aliased
from typing import List, Dict
from collections import defaultdict

from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from app.schemas.workout_schema import ExerciseHistoryItem
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


async def get_exercise_history_for_workout(
    db: AsyncSession,
    workout_id: int,
    user_id: UUID,
    limit_per_exercise: int = 10
) -> Dict[str, List[ExerciseHistoryItem]]:
    """
    Retrieves exercise history for all exercises in a workout.
    Groups results by exercise name and returns the last N entries for each exercise.
    
    Args:
        db: The asynchronous database session.
        workout_id: The ID of the workout to get exercise history for.
        user_id: The UUID of the user.
        limit_per_exercise: Maximum number of history entries per exercise.
    
    Returns:
        Dictionary mapping exercise names to their history items.
    """
    # First, get all exercises in the current workout to get their names
    current_workout_query = (
        select(Exercise.name)
        .distinct()
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            Workout.id == workout_id,
            Workout.user_id == user_id
        )
    )
    
    result = await db.execute(current_workout_query)
    exercise_names = result.scalars().all()
    
    if not exercise_names:
        return {}
    
    # Get history for these exercise names across all user's workouts
    history_query = (
        select(
            Exercise.name,
            Workout.name.label('workout_name'),
            Workout.date_created.label('workout_date'),
            Set.completed_at,
            Set.weight,
            Set.reps,
            Set.duration,
            Set.distance,
            Set.id.label('set_id')
        )
        .select_from(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            and_(
                Exercise.name.in_(exercise_names),
                Workout.user_id == user_id,
                Set.status == SetStatus.done,
                Set.completed_at.isnot(None)
            )
        )
        .order_by(
            Exercise.name,
            desc(Set.completed_at)
        )
    )
    
    result = await db.execute(history_query)
    rows = result.all()
    
    # Group by exercise name and limit results
    history_by_exercise: Dict[str, List[ExerciseHistoryItem]] = defaultdict(list)
    
    for row in rows:
        exercise_name = row.name
        
        # Skip if we already have enough entries for this exercise
        if len(history_by_exercise[exercise_name]) >= limit_per_exercise:
            continue
            
        history_item = ExerciseHistoryItem(
            exercise_name=exercise_name,
            workout_name=row.workout_name,
            workout_date=row.workout_date,
            completed_at=row.completed_at,
            weight=row.weight,
            reps=row.reps,
            duration=row.duration,
            distance=row.distance,
            set_id=row.set_id
        )
        
        history_by_exercise[exercise_name].append(history_item)
    
    return dict(history_by_exercise)


async def get_workout_history_map(
    workout: Workout,
    db: AsyncSession,
    limit_per_exercise: int = 5
) -> Dict[str, List[ExerciseHistoryItem]]:
    """
    Gets exercise history for all exercises in a workout as a map.
    
    Args:
        workout: The workout object to get history for
        db: The asynchronous database session
        limit_per_exercise: Maximum number of history entries per exercise
    
    Returns:
        Dictionary mapping exercise names to their history
    """
    # Get all unique exercise names from the workout
    exercise_names = set()
    for block in workout.blocks:
        for exercise in block.exercises:
            exercise_names.add(exercise.name)
    
    if not exercise_names:
        return {}
    
    # Get history for all exercises in one query
    history_query = (
        select(
            Exercise.name,
            Workout.name.label('workout_name'),
            Workout.date_created.label('workout_date'),
            Set.completed_at,
            Set.weight,
            Set.reps,
            Set.duration,
            Set.distance,
            Set.id.label('set_id')
        )
        .select_from(Set)
        .join(Exercise, Set.exercise_id == Exercise.id)
        .join(Block, Exercise.block_id == Block.id)
        .join(Workout, Block.workout_id == Workout.id)
        .where(
            and_(
                Exercise.name.in_(exercise_names),
                Workout.user_id == workout.user_id,
                Set.status == SetStatus.done,
                Set.completed_at.isnot(None),
                Workout.id != workout.id  # Exclude current workout
            )
        )
        .order_by(
            Exercise.name,
            desc(Set.completed_at)
        )
    )
    
    result = await db.execute(history_query)
    rows = result.all()
    
    # Group by exercise name
    history_by_exercise: Dict[str, List[ExerciseHistoryItem]] = defaultdict(list)
    
    for row in rows:
        exercise_name = row.name
        
        # Skip if we already have enough entries for this exercise
        if len(history_by_exercise[exercise_name]) >= limit_per_exercise:
            continue
            
        history_item = ExerciseHistoryItem(
            exercise_name=exercise_name,
            workout_name=row.workout_name,
            workout_date=row.workout_date,
            completed_at=row.completed_at,
            weight=row.weight,
            reps=row.reps,
            duration=row.duration,
            distance=row.distance,
            set_id=row.set_id
        )
        
        history_by_exercise[exercise_name].append(history_item)
    
    return dict(history_by_exercise)


