from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.schemas.create_workout_schemas import WorkoutSchema
from app.llm.utils.langchain_utils import load_prompt
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Dict, Any

PROMPT_FILE = "workout_revision_prompt.md"

async def revise_workout(
    existing_workout: Dict[str, Any],
    user_feedback: str,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None
) -> WorkoutSchema:
    """
    Überarbeitet ein bestehendes Workout basierend auf User-Feedback.
    
    Args:
        existing_workout: Das bestehende Workout als Dictionary
        user_feedback: Feedback/Kommentar des Users zur gewünschten Änderung
        training_plan: Optionaler Trainingsplan als Kontext
        training_history: Optionale Trainingshistorie als JSON-String
    
    Returns:
        WorkoutSchema: Das überarbeitete Workout
    """
    try:
        # Load the prompt template
        prompt_template_content = load_prompt(PROMPT_FILE)

        # Convert existing workout to JSON string for the prompt
        existing_workout_json = json.dumps(existing_workout, indent=2, ensure_ascii=False, default=str)

        # Format the prompt with all available data
        formatted_prompt = prompt_template_content.format(
            existing_workout=existing_workout_json,
            user_feedback=user_feedback,
            training_plan=training_plan if training_plan is not None else "",
            training_history=training_history if training_history is not None else "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # Get API key from config
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)
        
        # Create chain with structured output
        chain = llm.with_structured_output(WorkoutSchema)
        
        # Debugging: Store the formatted prompt in a markdown file
        # with open("formatted_revision_prompt.md", "w") as f:
        #     f.write(formatted_prompt)
        
        print("Sending workout revision request to OpenAI API...")
        # Send the formatted prompt to the LLM
        revised_workout_schema = await chain.ainvoke(formatted_prompt)
        print("Received workout revision response from OpenAI API")

        return revised_workout_schema

    except Exception as e:
        print(f"Error in revise_workout: {e}")
        import traceback
        traceback.print_exc()
        raise 