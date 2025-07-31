"""
Minimale Workout Generation Chain für v1.
Generiert strukturierten JSON-Output mit minimalem Schema.
"""

from datetime import datetime
from typing import Optional, Tuple
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from .prompt import prepare_minimal_prompt
from .schemas import MinimalWorkoutSchema


def execute_workout_generation_minimal(
    training_plan_obj,
    training_profile,
    training_history_str: Optional[str] = None,
    user_prompt: Optional[str] = None,
    exercise_library_str: str = "",
) -> Tuple[str, MinimalWorkoutSchema]:
    """
    Führt die minimale Workout-Generation aus.
    
    Returns:
        Tuple[prompt, workout]: Prompt und strukturiertes Workout-Objekt
    """
    _start_total = datetime.now()
    
    print("🏋️ Minimal Workout Generation V1 (JSON Output)")
    print("🔧 Prompt Version:", os.environ.get("WORKOUT_PROMPT_VERSION", "FULL"))
    print("=" * 60)
    
    # Prompt vorbereiten (nutzt die minimal-spezifische Version)
    full_prompt = prepare_minimal_prompt(
        user_prompt=user_prompt,
        training_goals=training_plan_obj,
        environment_profile=training_profile,
        training_history=training_history_str,
        exercise_library=exercise_library_str,
    )
    
    print("📝 Prompt prepared, calling LLM...")
    
    # API Key holen
    api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("No API key found. Please set GEMINI_API_KEY or GOOGLE_API_KEY")
    
    # LLM mit strukturiertem Output aufrufen
    try:
        base_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            thinking_budget=1024
        )
        
        # Use structured output for JSON parsing
        llm_with_structure = base_llm.with_structured_output(MinimalWorkoutSchema)
        
        # Call LLM and get structured response
        workout_structured = llm_with_structure.invoke(full_prompt)
        
        print("✅ Workout generated successfully!")
        
    except Exception as e:
        print(f"❌ Error during LLM call: {e}")
        raise
    
    # Timing
    _total_duration = (datetime.now() - _start_total).total_seconds()
    print(f"⏱️  Total generation time: {_total_duration:.1f}s")
    print("=" * 60)
    
    return full_prompt, workout_structured