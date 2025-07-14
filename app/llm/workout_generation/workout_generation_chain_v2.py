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

from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
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

    def _load_full_prompt_template(self) -> PromptTemplate:
        """Loads the complete prompt template for workout generation."""
        prompt_path = Path(__file__).parent / "prompts" / "workout_generation_prompt.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return PromptTemplate.from_template(content, template_format="f-string")


    def load_structure_prompt(self) -> PromptTemplate:
        """Lade den Strukturierungs-Prompt."""
        prompt_path = Path(__file__).parent / "prompts" / "workout_generation_prompt_step2.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return PromptTemplate.from_template(content, template_format="f-string")

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
    
    async def structure_workout(self, freeform_text: str) -> WorkoutSchema:
        """Strukturiere das Freeform-Workout zu einem JSON-Schema."""
        print("🔄 Strukturiere Workout...")
        
        structure_prompt = self.load_structure_prompt()
        
        # Strukturiere mit Google AI
        structured_workout = await (
            structure_prompt | self.structure_llm
        ).ainvoke({"FREEFORM_WORKOUT_PLACEHOLDER": freeform_text})
        
        print("✅ Workout strukturiert")
        return structured_workout
    
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
    only_freeform_generation: bool = False,
    db_manager: Optional[DatabaseManager] = None, # Changed type from AsyncSession to DatabaseManager
) -> Union[WorkoutSchema, str]:
    """
    Hauptfunktion für Workout-Generierung mit einem modularen Prompt.
    
    Workflow:
    1. Erstelle einen vollständigen Prompt mit allgemeinen und spezifischen Workout-Daten.
    2. Generiere das Workout als Freitext.
    3. Strukturiere das Ergebnis (optional).
    
    Args:
        training_plan_str (Optional[str]): Formatierter Trainingsplan als String.
        training_history (Optional[List[Workout]]): Liste der Workout-Objekte aus der Historie.
        user_prompt (Optional[str]): Der spezifische User-Prompt für das Workout.
        only_freeform_generation (bool): Wenn True, wird nur der Freiform-Text generiert und zurückgegeben.
        
    Returns:
        Union[WorkoutSchema, str]: Strukturiertes Workout-Schema oder der unstrukturierte Freiform-Text, 
                                   abhängig vom `only_freeform_generation` Flag.
    """
    _start_total = datetime.now()
    
    print("🏋️ Streamlined Workout Generation V2")
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
    
    # Step 1: Generate freeform workout
    print("🔄 Step 1: Generating freeform workout...")
    freeform_text = await chain.generate_freeform_workout(chain_inputs=chain_inputs)
    
    # Document the intermediate freeform workout
    freeform_prompt_template = chain._load_full_prompt_template()
    chain._document_llm_interaction(
        "freeform_generation", freeform_prompt_template, chain_inputs, freeform_text
    )

    if only_freeform_generation:
        print("⚠️ Only freeform generation requested. Skipping structuring step.")
        _total_duration = (datetime.now() - _start_total).total_seconds()
        print(f"⏱️  Total generation time: {_total_duration:.1f}s")
        print("=" * 70)
        return freeform_text

    # Step 2: Structure the workout
    print("🔄 Step 2: Structuring with Google AI...")
    structured_workout = await chain.structure_workout(freeform_text)
    
    # Detailed workout output
    _total_duration = (datetime.now() - _start_total).total_seconds()
    
    print("✅ Workout Generation V2 complete!")
    print(f"⏱️  Total generation time: {_total_duration:.1f}s")
    print("=" * 70)
    
    # Document final results
    structure_prompt_template = chain.load_structure_prompt()
    chain._document_llm_interaction(
        "final_workout", structure_prompt_template, {"FREEFORM_WORKOUT_PLACEHOLDER": freeform_text}, structured_workout
    )
    
    return structured_workout 