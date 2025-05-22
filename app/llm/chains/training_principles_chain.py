from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.utils.langchain_utils import load_prompt
from app.core.config import get_config
from datetime import date
import json
from app.llm.schemas.training_principles_schemas import TrainingPrinciplesSchema

PROMPT_FILE = "training_principles_prompt.md"

async def generate_training_principles(training_goals: dict | None = None) -> TrainingPrinciplesSchema:
    """
    Leitet aus den Trainingszielen professionelle Trainingsprinzipien als strukturiertes JSON ab.
    Enthält Personenübersicht, Kernprinzipien, Trainingsempfehlungen und Trainingsphasen.
    """
    try:
        training_goals_json = json.dumps(training_goals, ensure_ascii=False, indent=2, default=str) if training_goals else None
        current_date_iso = date.today().isoformat()
        
        prompt_template = load_prompt(PROMPT_FILE)
        prompt = prompt_template.format(
            training_goals=training_goals_json or "{}",
            current_date=current_date_iso
        )

        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        llm = ChatOpenAI(model="gpt-4.1", api_key=OPENAI_API_KEY)

        # Explicitly specify function calling as the method
        structured_llm = llm.with_structured_output(
            TrainingPrinciplesSchema,
            method="function_calling"  # Use function calling instead of default structured output
        )
        
        print("Sending request to OpenAI API for training principles (structured JSON output)...")
        principles_schema = await structured_llm.ainvoke(prompt)
        print("Received structured response from OpenAI API")
        
        return principles_schema
    except Exception as e:
        print(f"Error in generate_training_principles: {e}")
        import traceback
        traceback.print_exc()
        raise 