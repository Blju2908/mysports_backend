from uuid import UUID
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import exists, and_
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus


async def load_workouts_for_user(
    user_id: UUID,
    db: AsyncSession,
    limit: int | None = None,
    workout_id: int | None = None,
    only_with_completed_sets: bool = True,
) -> List[Workout] | Workout | None:
    """
    ✅ SQLModel Best Practice: Loads workouts for a user using direct user_id relationship.
    
    If workout_id is provided, loads that specific workout.
    Otherwise, loads the latest 'limit' workouts for the user.
    Eagerly loads blocks, exercises, and sets.
    """
    base_query = (
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(Workout.user_id == user_id)
    )

    if workout_id is not None:
        # ✅ Single workout - use db.scalar() one-liner
        return await db.scalar(base_query.where(Workout.id == workout_id))
    
    # Multiple workouts
    if only_with_completed_sets:
        # Only include workouts that have at least one completed set
        subquery = exists().where(
            and_(
                Set.status == SetStatus.done,
                Set.exercise_id == Exercise.id,
                Exercise.block_id == Block.id,
                Block.workout_id == Workout.id
            )
        )
        base_query = base_query.where(subquery)
    
    base_query = base_query.order_by(Workout.date_created.desc())
    
    if limit is not None:
        base_query = base_query.limit(limit)
    
    # ✅ Multiple results - use db.scalars()
    result = await db.scalars(base_query)
    return result.all()


async def get_user_workout_history(user_id: UUID, db: AsyncSession, limit: int = 10) -> List[Workout]:
    """
    ✅ SQLModel Best Practice: Fetches completed workouts for a user.
    Uses direct user_id relationship and eager loading.
    """
    # ✅ Direct query with eager loading
    subquery = exists().where(
        and_(
            Set.status == SetStatus.done,
            Set.exercise_id == Exercise.id,
            Exercise.block_id == Block.id,
            Block.workout_id == Workout.id
        )
    )
    
    result = await db.scalars(
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(Workout.user_id == user_id)
        .where(subquery)
        .order_by(Workout.date_created.desc())
        .limit(limit)
    )
    
    workouts = result.all()
    
    # Post-process to filter only completed sets
    filtered_workouts = []
    for workout in workouts:
        filtered_workout = Workout(
            id=workout.id,
            user_id=workout.user_id,
            training_plan_id=workout.training_plan_id,
            name=workout.name,
            date_created=workout.date_created,
            description=workout.description,
            duration=workout.duration,
            focus=workout.focus,
            notes=workout.notes,
            blocks=[]
        )
        
        # Filter blocks and exercises with completed sets
        for block in workout.blocks:
            filtered_block = Block(
                id=block.id,
                workout_id=block.workout_id,
                name=block.name,
                description=block.description,
                notes=block.notes,
                exercises=[]
            )
            
            has_completed_exercises = False
            for exercise in block.exercises:
                completed_sets = [s for s in exercise.sets if s.status == SetStatus.done]
                if completed_sets:
                    filtered_exercise = Exercise(
                        id=exercise.id,
                        name=exercise.name,
                        notes=exercise.notes,
                        block_id=exercise.block_id,
                        sets=completed_sets
                    )
                    filtered_block.exercises.append(filtered_exercise)
                    has_completed_exercises = True
            
            if has_completed_exercises:
                filtered_workout.blocks.append(filtered_block)
        
        if filtered_workout.blocks:
            filtered_workouts.append(filtered_workout)
    
    return filtered_workouts


# ✅ SQLModel Best Practice: Remove unnecessary wrapper function
# get_training_history_for_user_from_db is now just an alias
get_training_history_for_user_from_db = get_user_workout_history
