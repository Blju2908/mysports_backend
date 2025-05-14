from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.schemas.create_workout_schemas import WorkoutSchema
from app.llm.utils.langchain_utils import load_prompt
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional

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
        # training_history (jetzt JSON-String) wird direkt verwendet.

        prompt_template_content = load_prompt(PROMPT_FILE)

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

        # llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)
        llm = ChatOpenAI(model="gpt-4.1", api_key=OPENAI_API_KEY) 

        # Nutze with_structured_output mit async=True
        # The prompt itself is now already formatted and contains all instructions.
        chain = llm.with_structured_output(WorkoutSchema) 
        
        # Debugging: Store the formatted prompt in a markdown file
        with open("formatted_prompt.md", "w") as f:
            f.write(formatted_prompt)
        
        print("Sending request to OpenAI API...")
        # We pass the fully formatted prompt directly.
        # The ChatPromptTemplate.from_template was redundant if the prompt string is already complete.
        workout_schema_instance = await chain.ainvoke(formatted_prompt)
        print("Received response from OpenAI API")

        return workout_schema_instance

    except Exception as e:
        print(f"Error in generate_workout: {e}")
        import traceback

        traceback.print_exc()
        raise
