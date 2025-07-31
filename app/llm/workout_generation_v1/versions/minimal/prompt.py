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
    prompt_file = Path(__file__).parent / "prompts" / "workout_generation_prompt_minimal.md"
    
    if not prompt_file.exists():
        # Fallback to a simple prompt if file doesn't exist
        return f"""Du bist ein Fitness-Experte. Erstelle ein kurzes Workout basierend auf:

User Request: {user_prompt}

Training Goals: {training_goals}
Environment: {environment_profile}
Training History: {training_history}

Available Exercises:
{exercise_library}

Erstelle ein strukturiertes Workout im Markdown-Format."""

    with open(prompt_file, "r", encoding="utf-8") as file:
        template_content = file.read()
    
    # Simple string replacement (no Langchain needed for minimal version)
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    prompt = template_content.format(
        current_date=current_date,
        user_prompt=user_prompt,
        training_goals=training_goals,
        training_profile=environment_profile,
        training_history=training_history or "Keine Trainingshistorie verfügbar",
        exercise_library=exercise_library,
    )
    
    return prompt