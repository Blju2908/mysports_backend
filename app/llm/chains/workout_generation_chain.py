from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..schemas.workout_generation_schema import (
    WorkoutSchema,
)
from ..utils.langchain_utils import load_prompt
import json
from app.core.config import get_config
from app.models.workout_model import WorkoutStatus
from datetime import datetime

PROMPT_FILE = "workout_generation_prompt.txt"

# LLM-Chain Funktion


async def generate_workout(
    training_plan,
    training_history=None,
    user_prompt: str = None
):
    """
    Generiert ein Workout mit LLM. Akzeptiert beliebiges Trainingsplan-Schema, optionale Historie und optionalen User Prompt.
    """
    try:
        if training_history is None:
            training_history = []
        # Trainingshistorie als JSON-String (ggf. gekürzt für Prompt)
        try:
            training_history_json = json.dumps(
                [entry.model_dump() for entry in training_history], indent=2, default=str
            )
        except Exception as e:
            print(f"Warning: Could not convert training history to JSON using model_dump: {e}")
            # Fallback für Demo-Objekte
            training_history_json = json.dumps(training_history, indent=2, default=str)
        
        # Trainingsplan als JSON-String
        try:
            training_plan_json = training_plan.model_dump_json(indent=2)
        except Exception as e:
            print(f"Warning: Could not convert training plan to JSON using model_dump_json: {e}")
            # Fallback für Demo-Objekte
            training_plan_json = json.dumps(training_plan, indent=2, default=str)
        
        prompt_template = load_prompt(PROMPT_FILE)        
    
        prompt = prompt_template.format(
            training_plan=training_plan_json,
            training_history=training_history_json,
            user_prompt=user_prompt or ""
        )
        
        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        
        llm = ChatOpenAI(
            model="gpt-4.1-mini",
            api_key=OPENAI_API_KEY
        )
        
        # Nutze with_structured_output mit async=True
        chain = (
            ChatPromptTemplate.from_template("{prompt}")
            | llm.with_structured_output(WorkoutSchema)
        )
        print("Sending request to OpenAI API...")
        workout = await chain.ainvoke({"prompt": prompt})  # ainvoke statt invoke
        print("Received response from OpenAI API")
    
        return workout
    
    except Exception as e:
        print(f"Error in generate_workout: {e}")
        import traceback
        traceback.print_exc()
        raise
