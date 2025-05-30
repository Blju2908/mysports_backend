from langchain_openai import ChatOpenAI
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional
import os
from pathlib import Path
PROMPT_FILE = "workout_generation_prompt.md"

# LLM-Chain Funktion


async def generate_workout(
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None
) -> WorkoutSchema:
    """
    Generiert ein Workout mit LLM. Akzeptiert Trainingsprinzipien als String, 
    optionale Trainingshistorie als JSON-String und optionalen User Prompt.
    """
    try:
        # Trainingsplan (jetzt trainings_principles als String) wird direkt verwendet.

        # Load the Prompt File        
        prompt_path = Path(__file__).parent / PROMPT_FILE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        # Ensure default empty strings if None, to avoid issues with .format
        # The prompt itself handles "optional" display logic.
        formatted_prompt = prompt_template_content.format(
            training_plan=training_plan if training_plan is not None else "",
            training_history=training_history if training_history is not None else "",
            user_prompt=user_prompt if user_prompt is not None else "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        reasoning = {
            "effort": "low",
            "summary": None
        }
        

        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY, use_responses_api=True, model_kwargs={"reasoning": reasoning})
        # llm = ChatOpenAI(model="gpt-4.1", api_key=OPENAI_API_KEY) 

        # Nutze with_structured_output mit async=True
        # The prompt itself is now already formatted and contains all instructions.
        chain = llm.with_structured_output(WorkoutSchema) 
        
        should_document_input = False
        if should_document_input:
            await document_input(formatted_prompt)
        
        print("Sending request to OpenAI API...")
        workout_schema_instance = await chain.ainvoke(formatted_prompt)
        print("Received response from OpenAI API")


        should_document_output = False
        if should_document_output:
            await document_output(workout_schema_instance)

        return workout_schema_instance

    except Exception as e:
        print(f"Error in generate_workout: {e}")
        import traceback

        traceback.print_exc()
        raise

async def document_output(workout_schema: WorkoutSchema) -> None:
    """
    Document the output of the workout generation chain.
    """
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "output")
        # check if folder "output" exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # create a file with the name of the user_prompt and the current date
        file_name = f"{datetime.now().strftime('%Y-%m-%d')}_workout_generation_output.json"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w") as f:
            f.write(workout_schema.model_dump_json())
    except Exception as e:
        print(f"Error in document_output: {e}")
        import traceback
        traceback.print_exc()
        raise
    
async def document_input(formatted_prompt: str) -> None:
    """
    Document the input of the workout generation chain.
    """
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "output")
        # check if folder "output" exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # create a file with the name of the user_prompt and the current date
        file_name = f"{datetime.now().strftime('%Y-%m-%d')}_workout_generation_input.md"
        file_path = os.path.join(output_dir, file_name)
        with open(file_path, "w") as f:
            f.write(formatted_prompt)
    except Exception as e:
        print(f"Error in document_input: {e}")
        import traceback
        traceback.print_exc()
        raise