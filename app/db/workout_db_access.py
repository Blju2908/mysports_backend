from uuid import UUID
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import exists, and_
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from app.models.training_plan_model import TrainingPlan


async def load_workouts_for_user(
    user_id: UUID,
    db: AsyncSession,
    limit: Optional[int] = None,
    workout_id: Optional[int] = None,
    only_with_completed_sets: bool = True,
) -> List[Workout] | Optional[Workout]:
    """
    Loads workouts for a user.

    If workout_id is provided, loads that specific workout.
    Otherwise, loads the latest 'limit' workouts for the user's current training plan.
    Eagerly loads blocks, exercises, and sets.
    """
    statement = (
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
    )

    if workout_id is not None:
        statement = statement.where(Workout.id == workout_id)
        result = await db.exec(statement)
        return result.one_or_none()
    else:
        plan_statement = select(TrainingPlan.id).where(TrainingPlan.user.has(id=user_id))
        plan_result = await db.exec(plan_statement)
        training_plan_id = plan_result.one_or_none()

        if not training_plan_id:
            return []

        statement = statement.where(Workout.training_plan_id == training_plan_id)
        if only_with_completed_sets:
            statement = statement.where(Set.status == SetStatus.done)
        statement = statement.order_by(Workout.date_created.desc())

        if limit is not None:
            statement = statement.limit(limit)
        
        result = await db.exec(statement)
        return result.all()

async def get_user_workout_history(user_id: UUID, db: AsyncSession, limit: int = 10) -> List[Workout]:
    """
    Fetches the last 'limit' workouts for a given user where at least one set has status 'done'.
    Only returns workouts that have been at least partially completed.
    Additionally, only includes blocks and exercises that have at least one completed set.
    """
    # First, get the user's training plan ID
    plan_statement = select(TrainingPlan.id).where(TrainingPlan.user.has(id=user_id))
    plan_result = await db.exec(plan_statement)
    training_plan_id = plan_result.one_or_none()
    
    if not training_plan_id:
        return []
    
    # Define a subquery that checks for the existence of at least one completed set in the workout
    # This uses exists() to check the condition through the hierarchy
    subquery = exists().where(
        and_(
            Set.status == SetStatus.done,
            Set.exercise_id == Exercise.id,
            Exercise.block_id == Block.id,
            Block.workout_id == Workout.id
        )
    )
    
    # Main query that selects workouts from user's training plan
    # and filters only those with at least one completed set
    statement = (
        select(Workout)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
            .selectinload(Exercise.sets)
        )
        .where(Workout.training_plan_id == training_plan_id)
        .where(subquery)
        .order_by(Workout.date_created.desc())
        .limit(limit)
    )
    
    result = await db.exec(statement)
    workouts = result.all()
    
    # Post-process the workouts to filter blocks and exercises
    filtered_workouts = []
    for workout in workouts:
        # Create a new workout object to avoid modifying the original
        filtered_workout = Workout(
            id=workout.id,
            training_plan_id=workout.training_plan_id,
            name=workout.name,
            date_created=workout.date_created,
            description=workout.description,
            duration=workout.duration,
            focus=workout.focus,
            notes=workout.notes,
            blocks=[]
        )
        
        # Filter blocks
        for block in workout.blocks:
            # Create a new block object
            filtered_block = Block(
                id=block.id,
                workout_id=block.workout_id,
                name=block.name,
                description=block.description,
                notes=block.notes,
                exercises=[]
            )
            
            # Filter exercises in this block
            has_completed_exercises = False
            for exercise in block.exercises:
                # Check if this exercise has any completed sets
                completed_sets = [s for s in exercise.sets if s.status == SetStatus.done]
                if completed_sets:
                    # Create a new exercise with only completed sets
                    filtered_exercise = Exercise(
                        id=exercise.id,
                        name=exercise.name,
                        notes=exercise.notes,
                        block_id=exercise.block_id,
                        sets=completed_sets
                    )
                    filtered_block.exercises.append(filtered_exercise)
                    has_completed_exercises = True
            
            # Only add the block if it has exercises with completed sets
            if has_completed_exercises:
                filtered_workout.blocks.append(filtered_block)
        
        # Only add the workout if it has blocks
        if filtered_workout.blocks:
            filtered_workouts.append(filtered_workout)
    
    return filtered_workouts


async def get_training_history_for_user_from_db(user_id: UUID, db: AsyncSession, limit: int = 10) -> List[Workout]:
    """
    Fetches the last 'limit' workouts for a given user to serve as training history.
    This is a convenience wrapper around load_workouts_for_user.
    """
    workouts = await get_user_workout_history(user_id=user_id, db=db, limit=limit)
    if isinstance(workouts, Workout): # Should not happen if limit is used without workout_id
        return [workouts]
    return workouts if workouts else []
