#!/usr/bin/env python3
"""
Skript zum Erstellen der Base Conversation für Workout-Generierung.
Lädt Trainingsprinzipien und Übungsbibliothek und erstellt eine Base Conversation.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
import json

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

# Imports
from app.core.config import get_config
from openai import AsyncOpenAI


class BaseConversationManager:
    """Verwaltet die Base Conversation für Workout-Generierung."""
    
    def __init__(self):
        self.config = get_config()
        self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY2)
        self.base_conversation_file = Path(__file__).parent / "base_conversation.json"
        self.base_prompt_file = Path(__file__).parent / "prompts" / "base_conversation_prompt.md"
        self.target_model = "gpt-4.1"

    def load_base_prompt(self) -> str:
        """Lade den zentralen Base Prompt aus der Datei."""
        if not self.base_prompt_file.exists():
            raise FileNotFoundError(f"Die Basis-Prompt-Datei wurde nicht gefunden: {self.base_prompt_file}")
        with open(self.base_prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def create_base_conversation(self) -> str:
        """Erstelle die Base Conversation mit OpenAI."""
        print("🔄 Erstelle Base Conversation aus zentraler Prompt-Datei...")
        
        try:
            with open(self.base_prompt_file, 'r', encoding='utf-8') as f:
                system_prompt = f.read()
            print(f"📝 System Prompt geladen ({len(system_prompt):,} Zeichen)")
            
            response = await self.client.responses.create(
                model=self.target_model,
                input=system_prompt
            )
            
            base_conversation_data = {
                "conversation_id": response.id,
                "created_at": datetime.now().isoformat(),
                "model": self.target_model,
                "system_prompt_length": len(system_prompt),
                "assistant_response": response.output_text,
                "usage": response.usage.model_dump() if response.usage else None
            }
            
            with open(self.base_conversation_file, 'w', encoding='utf-8') as f:
                json.dump(base_conversation_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Base Conversation Daten gespeichert: {self.base_conversation_file}")
            return response.id
            
        except Exception as e:
            print(f"❌ Fehler beim Erstellen der Base Conversation: {e}")
            return None

    def _validate_base_conversation_locally(self, data: dict) -> bool:
        """
        Validiert Base Conversation Daten lokal ohne API Call.
        Prüft auf Konsistenz des Modells und Alter der Datei.
        """
        print("🔍 Validiere Base Conversation lokal...")
        
        if not data:
            print("-  Validierung fehlgeschlagen: Keine Daten in base_conversation.json gefunden.")
            return False

        required_keys = ["conversation_id", "model", "created_at"]
        if not all(key in data for key in required_keys):
            print("-  Validierung fehlgeschlagen: Fehlende Schlüssel in base_conversation.json.")
            return False

        if data["model"] != self.target_model:
            print(f"-  Validierung fehlgeschlagen: Modell-Mismatch! Erwartet: {self.target_model}, Gefunden: {data['model']}.")
            return False

        try:
            created_at = datetime.fromisoformat(data["created_at"])
            if datetime.now() - created_at > timedelta(hours=24):
                print("-  Validierung fehlgeschlagen: Base Conversation ist älter als 24 Stunden.")
                return False
        except (ValueError, TypeError):
             print("-  Validierung fehlgeschlagen: Ungültiges Datumsformat in `created_at`.")
             return False
        
        print("✅ Lokale Validierung erfolgreich.")
        return True

    async def get_or_create_base_conversation(self) -> dict:
        """
        Hole oder erstelle die Base Conversation.
        Validiert lokal, ob eine bestehende Konversation wiederverwendet werden kann.
        """
        base_data = None
        if self.base_conversation_file.exists():
            with open(self.base_conversation_file, 'r', encoding='utf-8') as f:
                try:
                    base_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"⚠️ {self.base_conversation_file.name} ist korrupt oder leer.")
                    base_data = None

        if self._validate_base_conversation_locally(base_data):
            print(f"✅ Bestehende Base Conversation wird wiederverwendet: {base_data['conversation_id']}")
            return base_data
        else:
            print("⚠️ Base Conversation wird neu erstellt...")
            new_id = await self.create_base_conversation()
            if not new_id:
                raise Exception("Kritischer Fehler: Konnte keine neue Base Conversation erstellen.")
            
            with open(self.base_conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)


async def main():
    """Hauptfunktion zum Erstellen/Laden der Base Conversation."""
    print("🏋️ Base Conversation Manager für Workout-Generierung")
    print("=" * 50)
    
    manager = BaseConversationManager()
    
    try:
        conversation_data = await manager.get_or_create_base_conversation()
        conversation_id = conversation_data.get("conversation_id")
        print("\n" + "=" * 50)
        print(f"🎉 Base Conversation bereit: {conversation_id}")
        print("=" * 50)
        
        # Umgebungsvariable setzen für andere Skripte
        env_var = f"WORKOUT_BASE_CONVERSATION_ID={conversation_id}"
        print(f"\n💡 Füge diese Umgebungsvariable zu deiner .env hinzu:")
        print(f"   {env_var}")
        
        return conversation_id
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Base Conversation: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main()) 