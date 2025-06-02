from langchain_openai import ChatOpenAI
from app.core.config import get_config
from datetime import date
import json
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema
from pathlib import Path

PROMPT_FILE = "training_plan_generation_prompt.md"

async def generate_training_plan_generation(training_goals: dict | None = None) -> TrainingPlanGenerationSchema:
    """
    Leitet aus den Trainingszielen professionelle Trainingsprinzipien als strukturiertes JSON ab.
    Enthält Personenübersicht, Kernprinzipien, Trainingsempfehlungen und Trainingsphasen.
    """
    try:
        training_goals_json = json.dumps(training_goals, ensure_ascii=False, indent=2, default=str) if training_goals else None
        current_date_iso = date.today().isoformat()
        
        prompt_path = Path(__file__).parent / PROMPT_FILE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        prompt = prompt_template_content.format(
            training_goals=training_goals_json or "{}",
            current_date=current_date_iso
        )

        reasoning = {
            "effort": "low",
            "summary": None
        }

        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY, use_responses_api=True, model_kwargs={"reasoning": reasoning})

        # Explicitly specify function calling as the method
        structured_llm = llm.with_structured_output(
            TrainingPlanGenerationSchema,
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