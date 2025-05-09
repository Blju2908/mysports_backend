from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.schemas.create_workout_schemas import WorkoutSchema
from app.llm.utils.langchain_utils import load_prompt
import json
from app.core.config import get_config
from datetime import datetime

PROMPT_FILE = "workout_generation_prompt.md"

# LLM-Chain Funktion


async def generate_workout(
    training_plan=None, training_history=None, user_prompt: str = None
):
    """
    Generiert ein Workout mit LLM. Akzeptiert beliebiges Trainingsplan-Schema, optionale Historie und optionalen User Prompt.
    """
    try:
        # Trainingsplan als JSON-String
        try:
            if training_plan is not None:
                training_plan_json = training_plan.model_dump_json(indent=2)
            else:
                training_plan_json = None
        except Exception as e:
            raise RuntimeError(
                f"Could not convert training plan to JSON using model_dump_json: {e}"
            ) from e

        prompt_template = load_prompt(PROMPT_FILE)

        prompt = prompt_template.format(
            training_plan=training_plan_json,
            training_history=training_history,
            user_prompt=user_prompt or "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        # llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)
        llm = ChatOpenAI(model="gpt-4.1", api_key=OPENAI_API_KEY)

        # Nutze with_structured_output mit async=True
        chain = ChatPromptTemplate.from_template(
            "{prompt}"
        ) | llm.with_structured_output(WorkoutSchema)
        print("Sending request to OpenAI API...")
        workout = await chain.ainvoke({"prompt": prompt})
        print("Received response from OpenAI API")

        return workout

    except Exception as e:
        print(f"Error in generate_workout: {e}")
        import traceback

        traceback.print_exc()
        raise
