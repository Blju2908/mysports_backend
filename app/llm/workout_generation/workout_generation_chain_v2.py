"""
Streamlined workout generation.

Workflow:
1.  Create a comprehensive prompt with general principles and user-specific data.
2.  Generate a freeform workout using a powerful language model.
3.  Structure the result into a clean JSON schema with a fast, specialized model.
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List, Union
from pathlib import Path

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from sqlmodel.ext.asyncio.session import AsyncSession
from openai import AsyncOpenAI

from app.llm.workout_generation.create_workout_schemas import WorkoutSchema, CompactWorkoutSchema
from app.llm.workout_generation.workout_parser import convert_compact_to_verbose_schema
from app.core.config import get_config
from app.models.training_plan_model import TrainingPlan
from app.models.workout_model import Workout
from app.llm.workout_generation.exercise_filtering_service import (
    get_filtered_exercises_for_user,
    get_all_exercises_for_prompt,
)
from app.llm.workout_generation.create_workout_service import summarize_training_history
from app.llm.utils.db_utils import DatabaseManager # Import DatabaseManager


class WorkoutGenerationChainV2:
    """
    Streamlined workout generation.

    Workflow:
    1.  Create a comprehensive prompt with general principles and user-specific data.
    2.  Generate a freeform workout using a powerful language model.
    3.  Structure the result into a clean JSON schema with a fast, specialized model.
    """

    def __init__(self):
        self.config = get_config()
        self.freeform_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.config.GOOGLE_API_KEY,
            temperature=0.2,
        )
        self.structure_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=self.config.GOOGLE_API_KEY
        ).with_structured_output(WorkoutSchema)

    def _load_prompt_from_files(self, *file_paths: Path) -> PromptTemplate:
        """Loads and concatenates content from multiple prompt files."""
        full_content = ""
        for file_path in file_paths:
            with open(file_path, 'r', encoding='utf-8') as f:
                full_content += f.read() + "\n\n"
        return PromptTemplate.from_template(full_content, template_format="f-string")

    def _load_full_prompt_template(self) -> PromptTemplate:
        """Loads the complete prompt for freeform workout generation."""
        base_path = Path(__file__).parent / "prompts"
        return self._load_prompt_from_files(
            base_path / "workout_generation_prompt_base.md",
            base_path / "output_format_freeform.md",
        )

    def _load_json_prompt_template(self) -> PromptTemplate:
        """Loads the JSON prompt template for direct structured output."""
        base_path = Path(__file__).parent / "prompts"
        return self._load_prompt_from_files(
            base_path / "workout_generation_prompt_base.md",
            base_path / "output_format_json.md",
        )


    async def generate_freeform_workout(self, chain_inputs: Dict[str, Any]) -> str:
        """
        Generate a freeform workout using a single, complete prompt.

        Returns:
            str: The generated freeform text of the workout.
        """
        print("🔄 Creating full prompt...")
        full_prompt = self._load_full_prompt_template()

        chain = full_prompt | self.freeform_llm

        print(f"🤖 Generating freeform workout with {self.freeform_llm.model}...")

        try:
            response = await chain.ainvoke(chain_inputs)
            freeform_text = response.content

            print("✅ Freeform workout generated.")

            if response.response_metadata and 'token_usage' in response.response_metadata:
                usage = response.response_metadata['token_usage']
                print(f"📊 Token Usage (Gemini):")
                print(f"   Input Tokens:  {usage.get('prompt_token_count', 'N/A')}")
                print(f"   Output Tokens: {usage.get('candidates_token_count', 'N/A')}")
                print(f"   Total Tokens:  {usage.get('total_token_count', 'N/A')}")

            return freeform_text

        except Exception as e:
            print(f"❌ Error during freeform generation: {e}")
            raise ValueError(f"Workout generation failed: {e}")

    async def generate_structured_workout_directly(self, chain_inputs: Dict[str, Any]) -> CompactWorkoutSchema:
        """
        Generate a structured workout directly using a single, JSON-focused prompt.

        Returns:
            CompactWorkoutSchema: The compact, structured workout object from the LLM.
        """
        print("🔄 Creating JSON prompt...")
        json_prompt = self._load_json_prompt_template()

        # Chain to generate a compact, structured workout
        chain = json_prompt | self.freeform_llm.with_structured_output(CompactWorkoutSchema)

        print(f"🤖 Generating structured workout directly with {self.freeform_llm.model}...")

        try:
            compact_workout = await chain.ainvoke(chain_inputs)

            print("✅ Compact workout generated.")
            # Document the intermediate compact workout
            self._document_llm_interaction(
                "one_step_compact_generation", json_prompt, chain_inputs, compact_workout
            )

            # Temporarily disabled as per user request to inspect raw output
            # verbose_workout = convert_compact_to_verbose_schema(compact_workout)
            # print("✅ Workout parsed successfully.")

            return compact_workout

        except Exception as e:
            print(f"❌ Error during direct structured generation: {e}")
            raise ValueError(f"Direct workout generation failed: {e}")
    
    async def structure_workout(self, freeform_text: str) -> WorkoutSchema:
        """Strukturiere das Freeform-Workout zu einem JSON-Schema."""
        raise NotImplementedError("The two-step structuring process is currently disabled in favor of the one-step direct JSON generation.")
    
    def _document_llm_interaction(self, stage: str, prompt_template: PromptTemplate, inputs: Dict[str, Any], response: Any) -> None:
        """Dokumentiere die vollständige LLM-Interaktion."""
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)

            # --- Prompt-Formatierung (Vollständiger Prompt) ---
            prompt_path = out_dir / f"{ts}_{stage}_prompt.md"
            full_prompt_text = prompt_template.format(**inputs)
            
            prompt_content = f"# 🤖 Vollständiger Prompt für Stage: `{stage}`\n\n"
            prompt_content += f"**Timestamp:** {ts}\n\n---\n\n"
            prompt_content += full_prompt_text

            prompt_path.write_text(prompt_content, encoding="utf-8")

            # --- Response-Formatierung ---
            if isinstance(response, dict):
                output_text = json.dumps(response, indent=2, ensure_ascii=False)
                output_path = out_dir / f"{ts}_{stage}_response.json"
            elif hasattr(response, "model_dump_json"):
                output_text = response.model_dump_json(indent=2)
                output_path = out_dir / f"{ts}_{stage}_response.json"
            else:
                output_text = str(response)
                output_path = out_dir / f"{ts}_{stage}_response.md"

            output_path.write_text(output_text, encoding="utf-8")
            print(f"📝 Dokumentiert: {stage} ({prompt_path.name}, {output_path.name})")

        except Exception as e:
            print(f"❌ Dokumentation fehlgeschlagen: {e}")


# Globale Instanz für einfache Nutzung
_chain_instance: Optional[WorkoutGenerationChainV2] = None


def get_chain() -> WorkoutGenerationChainV2:
    """Hole oder erstelle die Chain-Instanz (Singleton)."""
    global _chain_instance
    if _chain_instance is None:
        _chain_instance = WorkoutGenerationChainV2()
    return _chain_instance


async def execute_workout_generation_sequence_v2(
    training_plan_str: Optional[str] = None,
    training_history: Optional[List[Workout]] = None,
    user_prompt: Optional[str] = None,
    generation_mode: str = "one-step", # Can be "one-step" or "two-step"
    db_manager: Optional[DatabaseManager] = None, # Changed type from AsyncSession to DatabaseManager
) -> Union[WorkoutSchema, CompactWorkoutSchema, str]:
    """
    Hauptfunktion für Workout-Generierung mit einem modularen Prompt.
    
    Workflow:
    - one-step: Generiert ein strukturiertes JSON-Workout direkt.
    - two-step: Generiert das Workout als Freitext und strukturiert es danach.
    
    Args:
        training_plan_str (Optional[str]): Formatierter Trainingsplan als String.
        training_history (Optional[List[Workout]]): Liste der Workout-Objekte aus der Historie.
        user_prompt (Optional[str]): Der spezifische User-Prompt für das Workout.
        generation_mode (str): The generation strategy to use.
        
    Returns:
        Union[WorkoutSchema, CompactWorkoutSchema, str]: Strukturiertes Workout-Schema oder der unstrukturierte Freiform-Text.
    """
    _start_total = datetime.now()
    
    print(f"🏋️ Streamlined Workout Generation V2 (Mode: {generation_mode})")
    print("=" * 60)

    summarized_history = "Keine Historie verfügbar"
    if training_history:
        print("🔄 Compressing training history...")
        summarized_history = summarize_training_history(training_history)
        print("✅ Training history compressed.")

    # Load exercise library
    exercise_library_str = ""
    if db_manager:
        print("🔄 Loading all exercises from database...")
        exercise_library_str = await get_all_exercises_for_prompt(db_manager)
        print(f"✅ Loaded {len(exercise_library_str.splitlines())} exercises from database.")
    else:
        print("⚠️ No database manager provided. Exercise library will be empty.")

    # Get chain instance
    chain = get_chain()
    
    # Prepare input data
    chain_inputs = {
        "training_plan": training_plan_str or "Keine Trainingsziele definiert",
        "training_history": summarized_history,
        "user_prompt": user_prompt or "Kein spezifischer Prompt",
        "current_date": datetime.now().strftime("%d.%m.%Y"),
        "exercise_library": exercise_library_str,
    }

    if generation_mode == "one-step":
        # Step 1 (Single Step): Generate structured workout directly
        print("🔄 Running One-Step Generation...")
        structured_workout = await chain.generate_structured_workout_directly(chain_inputs)
        
        # The structured workout is already documented inside generate_structured_workout_directly
        # self._document_llm_interaction(
        #     "final_workout_one_step", final_prompt_template, chain_inputs, structured_workout
        # )
        
        # The result is the raw CompactWorkoutSchema, as requested
        final_result = structured_workout

    elif generation_mode == "two-step":
        # Step 1: Generate freeform workout
        print("🔄 Running Two-Step Generation: Step 1 (Freeform)...")
        freeform_text = await chain.generate_freeform_workout(chain_inputs=chain_inputs)
        
        # Document the intermediate freeform workout
        freeform_prompt_template = chain._load_full_prompt_template()
        chain._document_llm_interaction(
            "freeform_generation", freeform_prompt_template, chain_inputs, freeform_text
        )

        # For now, the two-step process stops here and returns the freeform text.
        # The structuring step is disabled.
        print("⚠️ Two-step structuring is currently disabled. Returning freeform text.")
        final_result = freeform_text
    
    else:
        raise ValueError(f"Invalid generation_mode: '{generation_mode}'. Must be 'one-step' or 'two-step'.")

    # Detailed workout output
    _total_duration = (datetime.now() - _start_total).total_seconds()
    
    print("✅ Workout Generation V2 complete!")
    print(f"⏱️  Total generation time: {_total_duration:.1f}s")
    print("=" * 70)
    
    return final_result 