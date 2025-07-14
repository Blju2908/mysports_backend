"""
Streamlined workout generation.

Workflow:
1.  Create a comprehensive prompt with general principles and user-specific data.
2.  Generate a freeform workout using a powerful language model.
3.  Structure the result into a clean JSON schema with a fast, specialized model.
"""
from datetime import datetime
from typing import Optional, Dict, Any, List
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate

from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema
from app.core.config import get_config
from app.models.workout_model import Workout
from app.llm.workout_generation.workout_utils import summarize_training_history


def _load_prompt_from_files(*file_paths: Path) -> PromptTemplate:
    """Loads and concatenates content from multiple prompt files."""
    full_content = ""
    for file_path in file_paths:
        with open(file_path, 'r', encoding='utf-8') as f:
            full_content += f.read() + "\n\n"
    return PromptTemplate.from_template(full_content, template_format="f-string")

def _load_json_prompt_template() -> PromptTemplate:
    """Loads the JSON prompt template for direct structured output."""
    base_path = Path(__file__).parent / "prompts"
    return _load_prompt_from_files(
        base_path / "workout_generation_prompt_base.md",
        base_path / "output_format_json.md",
    )

async def execute_workout_generation_sequence_v2(
    training_plan_str: Optional[str] = None,
    training_history_str: Optional[str] = None,
    user_prompt: Optional[str] = None,
    exercise_library_str: str = "",
) -> CompactWorkoutSchema:
    """
    Executes the streamlined, one-step workout generation sequence.

    This function initializes the LLM, prepares the prompt, and invokes the chain
    to generate a structured workout based on the provided inputs.

    Args:
        training_plan_str (Optional[str]): Formatted training plan as a string.
        training_history_str (Optional[str]): Summarized training history as a string.
        user_prompt (Optional[str]): The specific user prompt for the workout.
        exercise_library_str (str): String representation of the exercise library.

    Returns:
        CompactWorkoutSchema: The structured workout object.
    """
    _start_total = datetime.now()
    print("🏋️ Streamlined Workout Generation V2 (Mode: One-Step)")
    print("=" * 60)

    # --- LLM and Prompt Setup ---
    config = get_config()
    base_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=config.GOOGLE_API_KEY,
        # Temperature is set to model default as requested.
        # For more consistent JSON, consider setting temperature to a low value e.g., 0.2
    )
    llm_with_structure = base_llm.with_structured_output(CompactWorkoutSchema)
    
    print("🔄 Creating JSON prompt...")
    json_prompt = _load_json_prompt_template()

    chain = json_prompt | llm_with_structure

    # --- Chain Execution ---
    print(f"🤖 Generating structured workout directly with {base_llm.model}...")
    
    chain_inputs = {
        "training_plan": training_plan_str or "Keine Trainingsziele definiert",
        "training_history": training_history_str or "Keine Historie verfügbar",
        "user_prompt": user_prompt or "Kein spezifischer Prompt",
        "current_date": datetime.now().strftime("%d.%m.%Y"),
        "exercise_library": exercise_library_str,
    }
    
    try:
        compact_workout = await chain.ainvoke(chain_inputs)
        print("✅ Compact workout generated.")
    except Exception as e:
        print(f"❌ Error during direct structured generation: {e}")
        raise ValueError(f"Direct workout generation failed: {e}")

    # --- Finalization ---
    _total_duration = (datetime.now() - _start_total).total_seconds()
    print("✅ Workout Generation V2 complete!")
    print(f"⏱️  Total generation time: {_total_duration:.1f}s")
    print("=" * 70)
    
    return compact_workout 