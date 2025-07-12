#!/usr/bin/env python3
"""
Skript zum Erstellen der Base Conversation für Workout-Generierung.
Lädt Trainingsprinzipien und Übungsbibliothek und erstellt eine Base Conversation.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
import json
import os

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

# Imports
from app.core.config import get_config
from app.llm.utils.db_utils import DatabaseManager
from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
from openai import AsyncOpenAI


class BaseConversationManager:
    """Verwaltet die Base Conversation für Workout-Generierung."""
    
    def __init__(self):
        self.config = get_config()
        self.client = AsyncOpenAI(api_key=self.config.OPENAI_API_KEY2)
        self.base_conversation_file = Path(__file__).parent / "base_conversation.json"
        self.base_prompt_file = Path(__file__).parent / "prompts" / "base_conversation_prompt.md"

    def load_base_prompt(self) -> str:
        """Lade den zentralen Base Prompt aus der Datei."""
        if not self.base_prompt_file.exists():
            raise FileNotFoundError(f"Die Basis-Prompt-Datei wurde nicht gefunden: {self.base_prompt_file}")
        with open(self.base_prompt_file, 'r', encoding='utf-8') as f:
            return f.read()
    
    async def create_base_conversation(self) -> str:
        """Erstelle die Base Conversation mit OpenAI."""
        print("🔄 Erstelle Base Conversation aus zentraler Prompt-Datei...")
        
        # Lade zentralen Prompt
        system_prompt = self.load_base_prompt()
        
        print(f"📝 System Prompt geladen ({len(system_prompt):,} Zeichen)")
        
        reasoning = {
            "effort": "low",
            "summary": None
        }

        # Erstelle Base Conversation
        response = await self.client.responses.create(
            model="o4-mini",
            input=system_prompt,
            reasoning=reasoning
        )
        
        conversation_id = response.id
        print(f"✅ Base Conversation erstellt: {conversation_id}")
        
        # Speichere Metadaten inkl. Inhalt
        metadata = {
            "conversation_id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "model": "gpt-4.1-mini",
            "system_prompt_length": len(system_prompt),
            "assistant_response": response.output_text,
            "usage": response.usage.model_dump() if response.usage else None
        }
        
        # Speichere in JSON-Datei
        with open(self.base_conversation_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Metadaten gespeichert: {self.base_conversation_file}")
        
        return conversation_id
    
    def load_base_conversation_id(self) -> str:
        """Lade die Base Conversation ID aus der Datei."""
        if not self.base_conversation_file.exists():
            return None
        
        with open(self.base_conversation_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            return metadata.get('conversation_id')
    
    async def validate_base_conversation(self, conversation_id: str) -> bool:
        """Prüfe, ob die Base Conversation noch gültig ist."""
        try:
            print(f"🔍 Validiere Base Conversation: {conversation_id}")
            
            # Teste mit einer einfachen Anfrage
            test_response = await self.client.responses.create(
                model="o4-mini",
                input="Status check - bist du bereit?",
                previous_response_id=conversation_id
            )
            
            print(f"✅ Base Conversation ist gültig: {test_response.output_text}")
            return True
            
        except Exception as e:
            print(f"❌ Base Conversation ist ungültig: {e}")
            return False
    
    async def get_or_create_base_conversation(self) -> str:
        """Hole oder erstelle die Base Conversation."""
        # Versuche bestehende zu laden
        conversation_id = self.load_base_conversation_id()
        
        if conversation_id:
            # Validiere bestehende Conversation
            if await self.validate_base_conversation(conversation_id):
                print(f"✅ Bestehende Base Conversation wiederverwendet: {conversation_id}")
                # Lade und gib die vollen Daten zurück
                with open(self.base_conversation_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                print("⚠️ Bestehende Base Conversation ungültig, erstelle neue...")
        
        # Erstelle neue Base Conversation
        await self.create_base_conversation()
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