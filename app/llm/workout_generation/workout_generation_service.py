"""
Gemeinsamer Service für Workout-Generation.
Eliminiert Code-Duplikation zwischen API-Endpoint und Scripts.
"""

from uuid import UUID
from typing import Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel

from app.models.training_plan_model import TrainingPlan, TrainingProfile
from app.services.workout_service import get_latest_workouts_with_details
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm
from app.llm.workout_generation.workout_utils import summarize_training_history
from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
from app.llm.workout_generation.workout_generation_chain_v2 import execute_workout_generation_sequence_v2
from app.llm.workout_generation_v1.utils.prepare_prompt import prepare_prompt


class WorkoutGenerationInput(BaseModel):
    """Input-Daten für die Workout-Generation."""
    user_id: UUID
    user_prompt: str
    profile_id: Optional[int] = None
    session_duration: Optional[int] = None


class WorkoutGenerationData(BaseModel):
    """Geladene DB-Daten für die Workout-Generation."""
    training_plan_id: Optional[int]
    formatted_training_plan: Optional[str]
    training_history: Optional[str]
    exercise_library: str
    environment_profile: Optional[TrainingProfile]
    training_plan_obj: Optional[TrainingPlan]


async def load_workout_generation_data(
    db: AsyncSession, 
    input_data: WorkoutGenerationInput
) -> WorkoutGenerationData:
    """
    Lädt alle benötigten Daten für die Workout-Generation aus der Datenbank.
    
    Returns:
        WorkoutGenerationData: Alle geladenen und formatierten Daten
    """
    
    # Training Profile laden
    environment_profile = None
    if input_data.profile_id:
        environment_profile = await db.scalar(
            select(TrainingProfile).where(TrainingProfile.id == input_data.profile_id)
        )
    
    # Training Plan laden
    training_plan_obj = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.user_id == input_data.user_id)
    )
    
    training_plan_id = None
    formatted_training_plan = None
    if training_plan_obj:
        training_plan_id = training_plan_obj.id
        
        # Session Duration Override wenn angegeben
        if input_data.session_duration is not None:
            training_plan_obj.session_duration = input_data.session_duration
            
        formatted_training_plan = format_training_plan_for_llm(training_plan_obj)
    
    # Training History laden
    raw_training_history = await get_latest_workouts_with_details(
        db=db, user_id=input_data.user_id, number_of_workouts=10
    )
    
    training_history = None
    if raw_training_history:
        training_history = summarize_training_history(raw_training_history)
    
    # Exercise Library laden
    exercise_library = await get_all_exercises_for_prompt(db)
    
    return WorkoutGenerationData(
        training_plan_id=training_plan_id,
        formatted_training_plan=formatted_training_plan,
        training_history=training_history,
        exercise_library=exercise_library,
        environment_profile=environment_profile,
        training_plan_obj=training_plan_obj
    )


async def generate_workout_from_data(
    input_data: WorkoutGenerationInput,
    generation_data: WorkoutGenerationData
):
    """
    Generiert ein Workout basierend auf den geladenen Daten.
    
    Args:
        input_data: User-Input und Konfiguration
        generation_data: Geladene DB-Daten
        
    Returns:
        Tuple[str, CompactWorkoutSchema]: (full_prompt, workout_schema)
    """
    
    # Vollständigen Prompt erstellen
    full_prompt = prepare_prompt(
        user_prompt=input_data.user_prompt,
        training_goals=generation_data.training_plan_obj,
        environment_profile=generation_data.environment_profile,
        training_history=generation_data.training_history,
        exercise_library=generation_data.exercise_library,
    )
    
    # LLM Workout Generation
    compact_workout_schema = await execute_workout_generation_sequence_v2(
        training_plan_str=generation_data.formatted_training_plan,
        training_history_str=generation_data.training_history,
        user_prompt=input_data.user_prompt,
        exercise_library_str=generation_data.exercise_library,
    )
    
    return full_prompt, compact_workout_schema


async def generate_workout_complete(
    db: AsyncSession,
    input_data: WorkoutGenerationInput
) -> Tuple[str, object, WorkoutGenerationData]:
    """
    Komplette Workout-Generation: Daten laden + LLM-Generation.
    
    Args:
        db: Database Session
        input_data: User Input und Konfiguration
        
    Returns:
        Tuple[str, CompactWorkoutSchema, WorkoutGenerationData]: 
        (full_prompt, workout_schema, generation_data)
    """
    
    # Step 1: DB-Daten laden
    generation_data = await load_workout_generation_data(db, input_data)
    
    # Step 2: Workout generieren
    full_prompt, workout_schema = await generate_workout_from_data(input_data, generation_data)
    
    return full_prompt, workout_schema, generation_data