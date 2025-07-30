from pathlib import Path
from langchain_core.prompts import PromptTemplate
from datetime import datetime
from app.llm.workout_generation_v1.create_workout_llm_call import create_workout_with_llm
"""
How does the workout generation work?

1. Load user training goals
2. Load user profile
3. Load training history
4. Prepare all the inputs
5. Load the prompt template
6. Insert everything into the prompt
7. Create LLM instance
8. Execute the chain
9. Store the output
"""

def load_local_inputs(base_dir: Path):
    
    # Load user training goals
    training_goals_path = base_dir / "training_goals.md"
    with open(training_goals_path, "r") as file:
        training_goals = file.read()

    # Load user profile
    user_profile_path = base_dir / "user_profile.md"
    with open(user_profile_path, "r") as file:
        user_profile = file.read()

    # Load training history
    training_history_path = base_dir / "training_history.md"
    with open(training_history_path, "r") as file:
        training_history = file.read()
    
    # Load prompt template
    prompt_template_path = base_dir / "prompt_template.md"
    with open(prompt_template_path, "r") as file:
        prompt_template = PromptTemplate.from_template(file.read())
    
    return training_goals, user_profile, training_history, prompt_template



def local_work_generation_main(api_key: str):
    base_dir_input = Path(__file__).parent / "local_test_files" / "input_v1"
    base_dir_output = Path(__file__).parent / "local_test_files" / "output_v1"
    
    # Load the local data
    training_goals, user_profile, training_history, prompt_template = load_local_inputs(base_dir_input)
    
    user_prompt = "Bitte plane für mich ein gutes Home Workout mit einer 24kg Kettlebell und einem Türreck."

    # get the current date
    current_date = datetime.now().strftime("%Y-%m-%d")


    print("Creating prompt...")
    # Fill the prompt template
    prompt = prompt_template.format(
        current_date=current_date,
        training_goals=training_goals,
        user_profile=user_profile,
        training_history=training_history,
        user_prompt=user_prompt,
    )

    # timestamp before prompt creation
    timestamp_before_llm_call = datetime.now()

    print("Calling LLM...")
    llm_output = create_workout_with_llm(api_key, prompt)
    
    # timestamp after prompt creation
    timestamp_after_llm_call = datetime.now()
    # duration of prompt creation
    duration_of_llm_call = timestamp_after_llm_call - timestamp_before_llm_call
    print(f"Duration of LLM call: {duration_of_llm_call.total_seconds()} seconds")
    print("Workout generation completed.")

    # Ensure the output directory exists before writing the file
    base_dir_output.mkdir(parents=True, exist_ok=True)
    timestamp_for_file_name = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    with open(base_dir_output / f"llm_output_{timestamp_for_file_name}.md", "w") as file:
        file.write(llm_output.content)
