from uuid import UUID
from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel # Added import for UserModel


async def load_workouts_for_user(
    user_id: UUID,
    db: AsyncSession,
    limit: Optional[int] = None,
    workout_id: Optional[int] = None,
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
        statement = statement.order_by(Workout.date_created.desc())

        if limit is not None:
            statement = statement.limit(limit)
        
        result = await db.exec(statement)
        return result.all()

async def get_training_history_for_user_from_db(user_id: UUID, db: AsyncSession, limit: int = 10) -> List[Workout]:
    """
    Fetches the last 'limit' workouts for a given user to serve as training history.
    This is a convenience wrapper around load_workouts_for_user.
    """
    workouts = await load_workouts_for_user(user_id=user_id, db=db, limit=limit)
    if isinstance(workouts, Workout): # Should not happen if limit is used without workout_id
        return [workouts]
    return workouts if workouts else []
