from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

PROMPT_FILE = "training_plan_revision_prompt.md"

async def revise_training_plan(
    current_training_plan: TrainingPlanGenerationSchema,
    user_request: str,
    user_context: Optional[str] = None
) -> TrainingPlanGenerationSchema:
    """
    Überarbeitet einen bestehenden Trainingsplan basierend auf Benutzeranfrage.
    
    Args:
        current_training_plan: Der aktuelle Trainingsplan als Schema
        user_request: Benutzeranfrage zur gewünschten Änderung
        user_context: Zusätzlicher Benutzerkontext oder Präferenzen
    
    Returns:
        TrainingPlanGenerationSchema: Der überarbeitete Trainingsplan
    """
    try:
        # Load the prompt template
        prompt_path = Path(__file__).parent / PROMPT_FILE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        # Convert current training plan to JSON string for the prompt
        current_plan_json = json.dumps(
            current_training_plan.model_dump(), 
            indent=2, 
            ensure_ascii=False, 
            default=str
        )

        # Format the prompt with all available data
        formatted_prompt = prompt_template_content.format(
            current_training_plan=current_plan_json,
            user_request=user_request,
            user_context=user_context if user_context is not None else "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # Get API key from config
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        # Use lower temperature for more predictable results
        reasoning = {
            "effort": "low",
            "summary": None
        }

        llm = ChatOpenAI(
            model="o4-mini", 
            api_key=OPENAI_API_KEY, 
            use_responses_api=True, 
            model_kwargs={"reasoning": reasoning}
            # Note: temperature is not supported with structured output on this model
        )
        
        # Create chain with structured output
        chain = llm.with_structured_output(TrainingPlanGenerationSchema)
        
        # Debugging: Store the formatted prompt in a markdown file (optional)
        # with open("formatted_training_plan_revision_prompt.md", "w") as f:
        #     f.write(formatted_prompt)
        
        print("[TrainingPlanRevision] Sending training plan revision request to OpenAI API...")
        # Send the formatted prompt to the LLM
        revised_plan_schema = await chain.ainvoke(formatted_prompt)
        print("[TrainingPlanRevision] Received training plan revision response from OpenAI API")

        return revised_plan_schema

    except Exception as e:
        print(f"[TrainingPlanRevision] Error in revise_training_plan: {e}")
        import traceback
        traceback.print_exc()
        raise 