from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema
from app.llm.utils.llm_documentation import document_llm_session, document_llm_input, document_llm_output
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

# V2 Single-step workout revision prompt
PROMPT_FILE_V2 = "workout_revision_prompt_v2.md"

# ============================================================
# Single-step workout revision V2: Clean implementation
# ============================================================

def _load_revision_prompt_v2() -> PromptTemplate:
    """Loads the unified revision prompt template."""
    prompt_path = Path(__file__).parent / "prompts" / PROMPT_FILE_V2
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return PromptTemplate.from_template(content, template_format="f-string")

async def execute_workout_revision_sequence_v2(
    existing_workout: Dict[str, Any],
    user_feedback: str,
    training_plan_str: Optional[str] = None,
    training_history_str: Optional[str] = None,
    exercise_library_str: str = "",
) -> CompactWorkoutSchema:
    """
    Executes the streamlined, single-step workout revision sequence.
    
    This function initializes the LLM, prepares the prompt, and invokes the chain
    to generate a revised workout based on the provided inputs.
    
    Args:
        existing_workout (Dict[str, Any]): Current workout as dictionary
        user_feedback (str): User's feedback/revision request
        training_plan_str (Optional[str]): Formatted training plan as a string
        training_history_str (Optional[str]): Summarized training history as a string
        exercise_library_str (str): String representation of the exercise library
        
    Returns:
        CompactWorkoutSchema: The revised workout object
    """
    _start_total = datetime.now()
    print("🔄 Streamlined Workout Revision V2 (Mode: Single-Step)")
    print("=" * 60)
    
    # --- LLM and Prompt Setup ---
    config = get_config()
    base_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GOOGLE_API_KEY,
        # Using model default temperature for creativity in revisions
    )
    llm_with_structure = base_llm.with_structured_output(CompactWorkoutSchema)
    
    print("🔄 Creating revision prompt...")
    revision_prompt = _load_revision_prompt_v2()
    
    chain = revision_prompt | llm_with_structure
    
    # --- Chain Execution ---
    print(f"🤖 Generating revised workout directly with {base_llm.model}...")
    
    # Convert existing workout to JSON string for the prompt
    existing_workout_json = json.dumps(existing_workout, indent=2, ensure_ascii=False, default=str)
    
    chain_inputs = {
        "current_date": datetime.now().strftime("%d.%m.%Y"),
        "existing_workout": existing_workout_json,
        "user_feedback": user_feedback,
        "training_plan": training_plan_str or "Keine Trainingsziele definiert",
        "training_history": training_history_str or "Keine Historie verfügbar",
        "exercise_library": exercise_library_str,
    }
    
    try:
        revised_workout = await chain.ainvoke(chain_inputs)
        print("✅ Revised workout generated.")
    except Exception as e:
        print(f"❌ Error during revision generation: {e}")
        raise ValueError(f"Workout revision failed: {e}")
    
    # --- Finalization ---
    _total_duration = (datetime.now() - _start_total).total_seconds()
    print("✅ Workout Revision V2 complete!")
    print(f"⏱️  Total revision time: {_total_duration:.1f}s")
    print("=" * 70)
    
    return revised_workout