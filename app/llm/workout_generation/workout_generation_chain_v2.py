"""
Neue Version der Workout-Generierung mit Base Conversation Forking.
Nutzt die OpenAI Responses API für effizienten Token-Verbrauch.
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
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
from app.llm.workout_generation.create_base_conversation import BaseConversationManager
from app.llm.workout_generation.create_workout_service import summarize_training_history


class WorkoutGenerationChainV2:
    """
    Neue Version der Workout-Generierung mit Base Conversation Forking.
    
    Workflow:
    1. Lade Base Conversation ID (erstellt von create_base_conversation.py)
    2. Fork Base Conversation mit spezifischen Workout-Daten
    3. Strukturiere das Ergebnis mit Google AI
    """
    
    def __init__(self):
        self.config = get_config()
        self.openai_client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY2)
        self.base_conversation_file = Path(__file__).parent / "base_conversation.json"
        self.structure_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=self.config.GOOGLE_API_KEY
        ).with_structured_output(WorkoutSchema)
        
    def load_base_conversation_data(self) -> Optional[Dict[str, Any]]:
        """Lade die gesamten Base Conversation Daten aus der JSON-Datei."""
        if not self.base_conversation_file.exists():
            return None
        
        try:
            with open(self.base_conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Fehler beim Laden der Base Conversation Daten: {e}")
            return None
    
    def load_structure_prompt(self) -> PromptTemplate:
        """Lade den Strukturierungs-Prompt."""
        prompt_path = Path(__file__).parent / "prompts" / "workout_generation_prompt_step2.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return PromptTemplate.from_template(content, template_format="f-string")
    
    def create_fork_prompt(self, chain_inputs: Dict[str, Any]) -> str:
        """Erstelle den Prompt für das Forking der Base Conversation."""
        return f"""
Erstelle jetzt ein personalisiertes Workout basierend auf folgenden Daten:

# Aktuelles Datum
{chain_inputs.get('current_date', datetime.now().strftime('%d.%m.%Y'))}

# User Prompt
{chain_inputs.get('user_prompt', 'Kein spezifischer Prompt')}

# Trainingsplan
{chain_inputs.get('training_plan', 'Keine Trainingsziele definiert')}

# Trainingshistorie
{chain_inputs.get('training_history', 'Keine Historie verfügbar')}

Befolge die Anweisungen aus dem Base-Prompt zur Erstellung und Formatierung des Workouts.
"""
    
    async def generate_freeform_workout(self, base_conversation_data: Dict[str, Any], chain_inputs: Dict[str, Any]) -> str:
        """
        Generiere Freeform-Workout durch Forking der Base Conversation.
        
        ⚠️ WICHTIG: Nutzt gecachte Tokens für Kostenersparnis!
        
        Returns:
            str: Der generierte Freeform-Text des Workouts
        """
        if not base_conversation_data or 'conversation_id' not in base_conversation_data:
            raise ValueError("Keine gültigen Base Conversation Daten übergeben.")
            
        base_conversation_id = base_conversation_data['conversation_id']
        print(f"🔄 Forking Base Conversation: {base_conversation_id}")
        
        # Erstelle Fork-Prompt
        fork_prompt = self.create_fork_prompt(chain_inputs)
        
        reasoning = {
            "effort": "low",
            "summary": None
        }
        
        try:
            # Fork die Base Conversation
            response = await self.openai_client.responses.create(
                model="o4-mini",
                input=fork_prompt,
                previous_response_id=base_conversation_id,
                reasoning=reasoning
            )
            
            print(f"✅ Freeform-Workout generiert (Fork ID: {response.id})")
            print(f"🔄 Token Usage: {response.usage.total_tokens}")
            
            return response.output_text
            
        except Exception as e:
            print(f"❌ Fehler beim Forking: {e}")
            raise ValueError(f"Base Conversation Fork fehlgeschlagen: {e}")
    
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
    
    def _document_llm_interaction(self, stage: str, prompt: Any, response: Any) -> None:
        """Dokumentiere LLM-Interaktion im Stil von workout_generation_chain.py."""
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)

            # --- Prompt-Formatierung ---
            prompt_path = out_dir / f"{ts}_{stage}_prompt.md"
            prompt_content = f"# 🤖 Prompt für Stage: `{stage}`\n\n"
            prompt_content += f"**Timestamp:** {ts}\n\n---\n\n"

            if isinstance(prompt, dict):
                for key, value in prompt.items():
                    section_title = key.replace('_', ' ').title()
                    icons = {
                        'Training Plan': '📋',
                        'Training History': '📊',
                        'User Prompt': '💬',
                        'Current Date': '📅'
                    }
                    icon = icons.get(section_title, '📄')
                    prompt_content += f"## {icon} {section_title}\n\n"

                    if key == 'training_history' and isinstance(value, str) and value.strip().startswith('['):
                        try:
                            history_data = json.loads(value)
                            prompt_content += "```json\n" + json.dumps(history_data, indent=2, ensure_ascii=False) + "\n```\n\n"
                        except json.JSONDecodeError:
                            prompt_content += f"```\n{value}\n```\n\n"
                    elif isinstance(value, str) and len(value) > 200:
                        prompt_content += f"```\n{value}\n```\n\n"
                    else:
                        prompt_content += f"**{value}**\n\n"
                    prompt_content += "---\n\n"
            else:
                prompt_content += f"```\n{str(prompt)}\n```\n\n"

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
) -> WorkoutSchema:
    """
    Hauptfunktion für Workout-Generierung mit Base Conversation Forking.
    
    ⚠️ NEUE VERSION: Nutzt gecachte Base Conversation für Kostenersparnis!
    
    Workflow:
    1. Lade Base Conversation ID
    2. Fork mit spezifischen Workout-Daten
    3. Strukturiere das Ergebnis
    
    Returns:
        WorkoutSchema: Strukturiertes Workout
    """
    _start_total = datetime.now()
    
    print("🏋️ Workout-Generierung V2 mit Base Conversation Forking")
    print("=" * 60)
    
    # NEU: Stelle eine gültige Base Conversation sicher
    print("🛡️  Prüfe und sichere Base Conversation...")
    manager = BaseConversationManager()
    base_conversation_data = await manager.get_or_create_base_conversation()
    print("✅ Base Conversation ist gültig und bereit.")

    summarized_history = "Keine Historie verfügbar"
    if training_history:
        print("🔄 Komprimiere Trainingshistorie...")
        summarized_history = summarize_training_history(training_history)
        print("✅ Trainingshistorie komprimiert.")
    
    # Hole Chain-Instanz
    chain = get_chain()
    
    # Bereite Input-Daten vor
    chain_inputs = {
        "training_plan": training_plan_str or "Keine Trainingsziele definiert",
        "training_history": summarized_history,
        "user_prompt": user_prompt or "Kein spezifischer Prompt",
        "current_date": datetime.now().strftime("%d.%m.%Y"),
    }
    
    # Schritt 1: Generiere Freeform-Workout durch Forking
    print("🔄 Schritt 1: Freeform-Generierung via Base Conversation Fork")
    freeform_text = await chain.generate_freeform_workout(
        base_conversation_data=base_conversation_data, 
        chain_inputs=chain_inputs
    )
    
    # NEU: Ausgabe und Dokumentation des Freeform-Workouts
    chain._document_llm_interaction("freeform_generation", chain_inputs, freeform_text)
    
    # Schritt 2: Strukturiere das Workout
    print("🔄 Schritt 2: Strukturierung mit Google AI")
    structured_workout = await chain.structure_workout(freeform_text)
    
    # Detaillierte Ausgabe des Workouts
    _total_duration = (datetime.now() - _start_total).total_seconds()
    
    print("✅ Workout-Generierung V2 abgeschlossen!")
    print(f"⏱️  Gesamte Generierungszeit: {_total_duration:.1f}s")
    print("=" * 70)
    
    # Dokumentiere die finalen Ergebnisse
    chain._document_llm_interaction("final_workout", chain_inputs, structured_workout)
    
    return structured_workout 