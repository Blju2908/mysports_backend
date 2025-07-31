"""
Minimaler Workout Generation Service für v1.
Standalone Service für Performance-Tests mit Markdown-Output.
"""

from uuid import UUID
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.models.training_plan_model import TrainingPlan, TrainingProfile
from app.services.workout_service import get_latest_workouts_with_details
from ...shared.parsing.workout_utils import summarize_training_history
from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
from .chain import execute_workout_generation_minimal


class MinimalWorkoutInput(BaseModel):
    """Input für minimale Workout-Generation."""
    user_id: UUID
    user_prompt: str
    profile_id: Optional[int] = None


class MinimalWorkoutOutput(BaseModel):
    """Output der minimalen Workout-Generation."""
    markdown_workout: str
    generation_time: float
    prompt_version: str
    exercise_count: Optional[int] = None




async def generate_minimal_workout(
    db: AsyncSession,
    input_data: MinimalWorkoutInput
) -> Tuple[str, str, float]:
    """
    Generiert ein minimales Workout mit Markdown-Output.
    
    Args:
        db: Database Session
        input_data: User Input
        
    Returns:
        Tuple[prompt, markdown_workout, generation_time]
    """
    import time
    
    start_time = time.time()
    
    # 1. Training Profile laden
    environment_profile = None
    if input_data.profile_id:
        environment_profile = await db.scalar(
            select(TrainingProfile).where(TrainingProfile.id == input_data.profile_id)
        )
    
    # 2. Training Plan laden
    training_plan_obj = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.user_id == input_data.user_id)
    )
    
    if not training_plan_obj:
        raise ValueError(f"Kein Training Plan für User {input_data.user_id} gefunden")
    
    # 3. Training History laden
    raw_training_history = await get_latest_workouts_with_details(
        db=db, user_id=input_data.user_id, number_of_workouts=10
    )
    
    training_history_str = None
    if raw_training_history:
        training_history_str = summarize_training_history(raw_training_history)
    
    # 4. Exercise Library laden
    exercise_library_str = await get_all_exercises_for_prompt(db)
    
    # 5. Workout generieren (gibt sowohl Prompt als auch Workout zurück)
    debug_prompt, markdown_workout = execute_workout_generation_minimal(
        training_plan_obj=training_plan_obj,
        training_profile=environment_profile,
        training_history_str=training_history_str,
        user_prompt=input_data.user_prompt,
        exercise_library_str=exercise_library_str,
    )
    
    generation_time = time.time() - start_time
    
    return debug_prompt, markdown_workout, generation_time