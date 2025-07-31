import re
from app.models.training_plan_model import TrainingProfile, TrainingPlan
from langchain_core.prompts import PromptTemplate
from pathlib import Path
from datetime import datetime
from enum import Enum

class PromptVersion(Enum):
    FULL = "workout_generation_prompt_base.md"
    MINIMAL = "workout_generation_prompt_minimal.md"

def prepare_prompt_versioned(
    user_prompt,
    training_goals: TrainingPlan,
    environment_profile: TrainingProfile,
    training_history,
    exercise_library,
    version: PromptVersion = PromptVersion.FULL,
):
    """
    Prepare the prompt for the LLM with version selection.
    
    Args:
        version: PromptVersion.FULL or PromptVersion.MINIMAL
    """

    base_dir_prompt = Path(__file__).parent.parent / "prompts" / version.value
    base_dir_output = Path(__file__).parent.parent / "local_test_files" / "system_prompts"

    # Load the prompt template
    with open(base_dir_prompt, "r") as file:
        raw_prompt_content = file.read()
        # Normalize whitespace: replace multiple newlines with one, then strip overall
        cleaned_prompt_content = re.sub(r'\n\s*\n', '\n\n', raw_prompt_content).strip()
        prompt_template = PromptTemplate.from_template(cleaned_prompt_content)

    # get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")
    
    # Fill the prompt template
    prompt = prompt_template.format(
        current_date=current_date,
        user_prompt=user_prompt,
        training_goals=training_goals,
        training_profile=environment_profile,
        training_history=training_history,
        exercise_library=exercise_library,
    )

    if True:
        # ensure the output directory exists
        base_dir_output.mkdir(parents=True, exist_ok=True)
        
        # get the current timestamp
        current_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Add version to filename
        version_suffix = "_minimal" if version == PromptVersion.MINIMAL else "_full"

        # output the prompt to a markdown file
        with open(base_dir_output / f"prompt_{current_timestamp}{version_suffix}.md", "w") as f:
            f.write(prompt)

    return prompt