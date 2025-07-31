"""
Prompt-Erstellung für die minimale Workout-Generation.
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from app.models.training_plan_model import TrainingPlan, TrainingProfile


def prepare_minimal_prompt(
    user_prompt: str,
    training_goals: TrainingPlan,
    environment_profile: Optional[TrainingProfile],
    training_history: Optional[str],
    exercise_library: str,
) -> str:
    """
    Erstellt den Prompt für das minimale Workout mit der minimal-spezifischen Template.
    """
    # Load the minimal prompt template
    current_dir = Path(__file__).parent
    prompt_file = current_dir / "prompts" / "workout_generation_prompt_minimal.md"
    output_format_file = current_dir / "prompts" / "output_format_json_minimal.md"
    
    if not prompt_file.exists():
        # Fallback to a simple prompt if file doesn't exist
        return f"""Du bist ein Fitness-Experte. Erstelle ein kurzes Workout basierend auf:

User Request: {user_prompt}

Training Goals: {training_goals}
Environment: {environment_profile}
Training History: {training_history}

Available Exercises:
{exercise_library}

Erstelle ein strukturiertes Workout im JSON-Format."""

    # Load main prompt template
    with open(prompt_file, "r", encoding="utf-8") as file:
        template_content = file.read()
    
    # Load output format template
    output_format_content = ""
    if output_format_file.exists():
        with open(output_format_file, "r", encoding="utf-8") as file:
            output_format_content = "\n\n---\n\n" + file.read()
    
    # Simple string replacement (no Langchain needed for minimal version)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Format the main prompt
    prompt = template_content.format(
        current_date=current_date,
        user_prompt=user_prompt,
        training_goals=training_goals,
        training_profile=environment_profile,
        training_history=training_history or "Keine Trainingshistorie verfügbar",
        exercise_library=exercise_library,
    )
    
    # Append output format instructions
    prompt += output_format_content
    
    return prompt