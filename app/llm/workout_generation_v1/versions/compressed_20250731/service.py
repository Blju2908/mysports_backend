from typing import List, Dict, Optional, Tuple, Union
from pathlib import Path
import json
import time
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.models.workout_model import Workout
from app.models.training_plan_model import TrainingPlan, TrainingProfile
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from app.models.block_model import Block
from ...shared.formatting.training_plan import format_training_plan_for_llm_v2
from ...shared.formatting.training_history import format_training_history_for_llm
from ...shared.formatting.training_history_compressed import format_training_history_compressed
from ...shared.exercise_library import get_all_exercises_for_prompt
from .chain import create_compressed_workout_chain, invoke_compressed_workout_chain
from .schemas import CompactWorkoutSchema, ArrayExerciseSchema, CompactBlockSchema


class CompressedWorkoutInput(BaseModel):
    """Input for compressed workout generation"""
    user_id: UUID
    user_prompt: str
    profile_id: Optional[int] = None
    google_api_key: Optional[str] = None
    session_duration: Optional[int] = None


class CompressedWorkoutOutput(BaseModel):
    """Output from compressed workout generation"""
    workout: Optional[CompactWorkoutSchema]
    markdown_workout: str
    generation_time: float
    exercise_count: int
    prompt_version: str = "compressed"
    token_reduction: str = "~90%"


async def load_prompt_templates() -> Dict[str, str]:
    """Load all prompt templates from the prompts directory"""
    prompts_dir = Path(__file__).parent / "prompts"
    templates = {}
    
    for prompt_file in prompts_dir.glob("*.md"):
        with open(prompt_file, "r", encoding="utf-8") as f:
            templates[prompt_file.stem] = f.read()
    
    return templates


async def format_equipment_constraints(available_equipment: List[Dict]) -> str:
    """Format available equipment for the prompt"""
    if not available_equipment:
        return "Keine spezifischen Equipment-Angaben"
    
    equipment_list = []
    for eq in available_equipment:
        if eq.get("weight"):
            equipment_list.append(f"- {eq['name']}: {eq['weight']}kg")
        else:
            equipment_list.append(f"- {eq['name']}")
    
    return "\n".join(equipment_list)


async def expand_compressed_exercise(exercise: Union[ArrayExerciseSchema, Dict]) -> List[Dict]:
    """
    Expand compressed exercise format to full database format.
    
    Args:
        exercise: Compressed exercise data
        
    Returns:
        List of expanded set dictionaries
    """
    if isinstance(exercise, dict):
        exercise = ArrayExerciseSchema(**exercise)
    
    # Determine number of sets
    num_sets = 0
    if exercise.reps:
        num_sets = len(exercise.reps)
    elif exercise.duration:
        num_sets = len(exercise.duration)
    elif exercise.distance:
        num_sets = len(exercise.distance)
    
    if num_sets == 0:
        return []
    
    # Expand single values to arrays
    weight_array = exercise.weight
    if isinstance(weight_array, (int, float)):
        weight_array = [weight_array] * num_sets
    elif weight_array is None:
        weight_array = [None] * num_sets
    
    rest_array = exercise.rest
    if isinstance(rest_array, int):
        rest_array = [rest_array] * num_sets
    elif rest_array is None:
        rest_array = [60] * num_sets  # Default 60s rest
    elif isinstance(rest_array, list) and len(rest_array) < num_sets:
        # If rest array is shorter than number of sets, extend with the last value
        rest_array = rest_array + [rest_array[-1]] * (num_sets - len(rest_array))
    
    # Create expanded sets
    sets = []
    for i in range(num_sets):
        set_data = {
            "position": i,
            "reps": exercise.reps[i] if exercise.reps else None,
            "weight": weight_array[i] if weight_array else None,
            "duration": exercise.duration[i] if exercise.duration else None,
            "distance": exercise.distance[i] if exercise.distance else None,
            "rest_time": rest_array[i] if rest_array else 60
        }
        sets.append(set_data)
    
    return sets


def format_compressed_workout_as_markdown(workout: CompactWorkoutSchema) -> str:
    """Convert compressed workout to readable markdown format"""
    markdown = f"""# {workout.name}

**Fokus:** {workout.focus}  
**Dauer:** {workout.duration_min} Minuten  
**Beschreibung:** {workout.description}

**Fokus-Begründung:** {workout.focus_derivation}
"""
    
    # Format blocks
    for block in workout.blocks:
        markdown += f"## {block.name} ({block.duration_min} Min)\n\n"
        
        exercise_num = 1
        current_superset = None
        
        for exercise in block.exercises:
            # Check if this is part of a superset
            if exercise.superset and exercise.superset != current_superset:
                current_superset = exercise.superset
                markdown += f"**Superset {current_superset}:**\n"
            
            # Format the exercise with appropriate indentation
            indent = "  " if exercise.superset else ""
            markdown += format_exercise_markdown(exercise, exercise_num, indent=indent)
            exercise_num += 1
        
        markdown += "\n"
    
    return markdown


def format_exercise_markdown(exercise: ArrayExerciseSchema, num: int, indent: str = "") -> str:
    """Format a single exercise as markdown"""
    result = f"{indent}**{num}. {exercise.name}**\n"
    
    # Format sets
    if exercise.reps:
        sets_str = format_sets_string(exercise.reps, "Wdh")
    elif exercise.duration:
        sets_str = format_sets_string(exercise.duration, "Sek")
    elif exercise.distance:
        sets_str = format_sets_string(exercise.distance, "m")
    else:
        sets_str = "Keine Sätze definiert"
    
    result += f"{indent}   - Sätze: {sets_str}\n"
    
    # Add weight if present
    if exercise.weight:
        if isinstance(exercise.weight, list):
            weight_str = " → ".join([f"{w}kg" for w in exercise.weight])
        else:
            weight_str = f"{exercise.weight}kg"
        result += f"{indent}   - Gewicht: {weight_str}\n"
    
    # Add rest
    if exercise.rest:
        if isinstance(exercise.rest, list):
            rest_str = " → ".join([f"{r}s" for r in exercise.rest])
        else:
            rest_str = f"{exercise.rest}s"
        result += f"{indent}   - Pause: {rest_str}\n"
    
    # Add notes
    if hasattr(exercise, 'note') and exercise.note:
        result += f"{indent}   - Hinweis: {exercise.note}\n"
    
    if hasattr(exercise, 'equipment_note') and exercise.equipment_note:
        result += f"{indent}   - Equipment: {exercise.equipment_note}\n"
    
    result += "\n"
    return result


def format_sets_string(values: List[int], unit: str) -> str:
    """Format array of values as readable string"""
    if all(v == values[0] for v in values):
        # All values are the same
        return f"{len(values)} × {values[0]} {unit}"
    else:
        # Values differ
        return " → ".join([f"{v} {unit}" for v in values])


async def generate_compressed_workout(
    input_data: CompressedWorkoutInput
) -> Tuple[str, CompressedWorkoutOutput]:
    """
    Generate a workout using the compressed array-based format.
    
    Args:
        input_data: Input parameters for workout generation
        
    Returns:
        Tuple of (full_prompt, workout_output)
    """
    start_time = time.time()
    
    # Load prompt templates
    templates = await load_prompt_templates()
    
    # Import here to avoid circular imports
    from app.db.session import create_session
    from sqlalchemy import select, desc, exists
    from sqlalchemy.orm import selectinload
    from app.models.workout_model import Workout
    from app.models.block_model import Block
    from app.models.set_model import Set, SetStatus
    
    # Create session only for database operations
    async with create_session() as db:
        # Get user training history workouts
        workout_query = (
            select(Workout)
            .where(
                Workout.user_id == input_data.user_id,
                exists(
                    select(Set.id)
                    .join(Exercise, Set.exercise_id == Exercise.id)
                    .join(Block, Exercise.block_id == Block.id)
                    .where(
                        Block.workout_id == Workout.id,
                        Set.status == SetStatus.done
                    )
                )
            )
            .options(
                selectinload(Workout.blocks)
                .selectinload(Block.exercises)
                .selectinload(Exercise.sets)
            )
            .order_by(desc(Workout.id))
            .limit(10)
        )
        
        result = await db.execute(workout_query)
        workouts = result.scalars().all()
        
        # Get training plan if profile_id provided
        training_plan_context = ""
        if input_data.profile_id:
            training_profile = await db.get(TrainingProfile, input_data.profile_id)
            if training_profile and training_profile.id:
                training_plan_query = select(TrainingPlan).where(TrainingPlan.user_id == input_data.user_id)
                training_plan_result = await db.execute(training_plan_query)
                training_plan = training_plan_result.scalar_one_or_none()

                if input_data.session_duration:
                    training_plan.session_duration = input_data.session_duration

                if training_plan:
                    training_plan_context = format_training_plan_for_llm_v2(
                        training_plan, training_profile
                    )
        
        # Load exercise library
        exercise_library = await get_all_exercises_for_prompt(db)
    
        # Format training history while session is still open
        training_history = format_training_history_compressed(workouts) or "Keine Trainingshistorie vorhanden."
    
    # Build the full prompt
    base_prompt_template = templates.get("workout_generation_prompt_base", "")
    output_format = templates.get("output_format_structured", "")
    
    # Format the base prompt with all variables
    base_prompt_formatted = base_prompt_template.format(
        current_date=datetime.now().strftime("%Y-%m-%d"),
        user_prompt=input_data.user_prompt,
        training_goals=training_plan_context,
        training_history=training_history,
        exercise_library=exercise_library
    )
    
    # Combine formatted base prompt with output format
    full_prompt = f"{base_prompt_formatted}\n\n{output_format}"
    
    # Create and invoke the chain
    chain = create_compressed_workout_chain(api_key=input_data.google_api_key)
    
    try:
        workout_schema = invoke_compressed_workout_chain(chain, full_prompt)
        
        # Convert to markdown
        markdown_workout = format_compressed_workout_as_markdown(workout_schema)
        
        # Count exercises
        exercise_count = 0
        for block in workout_schema.blocks:
            exercise_count += len(block.exercises)
        
        generation_time = time.time() - start_time
        
        output = CompressedWorkoutOutput(
            workout=workout_schema,
            markdown_workout=markdown_workout,
            generation_time=generation_time,
            exercise_count=exercise_count
        )
        
        return full_prompt, output
        
    except Exception as e:
        # Fallback response
        generation_time = time.time() - start_time
        error_output = CompressedWorkoutOutput(
            workout=None,
            markdown_workout=f"❌ Fehler bei der Workout-Generierung: {str(e)}",
            generation_time=generation_time,
            exercise_count=0
        )
        return full_prompt, error_output


async def parse_compressed_workout_to_db_models(
    workout_schema: CompactWorkoutSchema,
    user_id: UUID,
    training_plan_id: Optional[int] = None
) -> Workout:
    """
    Parse compressed workout schema to database models.
    
    Args:
        workout_schema: The compressed workout schema from LLM
        user_id: User ID for the workout
        training_plan_id: Optional training plan ID
        
    Returns:
        Workout model ready for database insertion
    """
    # Create the main workout
    workout = Workout(
        user_id=user_id,
        training_plan_id=training_plan_id,
        name=workout_schema.name,
        description=workout_schema.description,
        duration=workout_schema.duration_min,
        focus=workout_schema.focus,
        muscle_group_load=[],
        focus_derivation=workout_schema.focus_derivation,
        date_created=datetime.utcnow()
    )
    
    # Process each block
    for block_idx, block_schema in enumerate(workout_schema.blocks):
        block = Block(
            name=block_schema.name,
            description="",
            position=block_idx
        )
        
        # Process exercises in the block
        exercise_position = 0
        for exercise_schema in block_schema.exercises:
            # Handle unilateral exercises
            if "[unilateral]" in exercise_schema.name or "(rechts)" in exercise_schema.name or "(links)" in exercise_schema.name:
                # Exercise already split by LLM
                exercises_to_add = [(exercise_schema, exercise_schema.name)]
            elif any(unilateral_marker in exercise_schema.name.lower() for unilateral_marker in ["single", "einarmig", "einbeinig", "unilateral"]):
                # Need to split into left/right
                base_name = exercise_schema.name
                exercises_to_add = [
                    (exercise_schema, f"{base_name} (rechts)"),
                    (exercise_schema, f"{base_name} (links)")
                ]
            else:
                # Regular exercise
                exercises_to_add = [(exercise_schema, exercise_schema.name)]
            
            # Create exercise(s)
            for ex_schema, ex_name in exercises_to_add:
                exercise = Exercise(
                    name=ex_name,
                    position=exercise_position,
                    superset_id=ex_schema.superset if ex_schema.superset else None,
                    notes=ex_schema.note if hasattr(ex_schema, 'note') and ex_schema.note else None
                )
                
                # Expand compressed sets
                sets_data = await expand_compressed_exercise(ex_schema)
                
                # Create Set objects
                for set_idx, set_data in enumerate(sets_data):
                    set_obj = Set(
                        weight=set_data.get("weight"),
                        reps=set_data.get("reps"),
                        duration=set_data.get("duration"),
                        distance=set_data.get("distance"),
                        rest_time=set_data.get("rest_time", 60),
                        position=set_idx
                    )
                    exercise.sets.append(set_obj)
                
                block.exercises.append(exercise)
                exercise_position += 1
        
        workout.blocks.append(block)
    
    return workout