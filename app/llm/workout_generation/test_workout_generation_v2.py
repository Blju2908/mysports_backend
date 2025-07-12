#!/usr/bin/env python3
"""
Test-Skript für die neue V2 Workout-Generierung mit Base Conversation Forking.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import UUID

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

# Imports
from app.llm.utils.db_utils import DatabaseManager
from app.llm.workout_generation.workout_generation_chain_v2 import execute_workout_generation_sequence_v2
from app.llm.workout_generation.create_workout_service import (
    format_training_plan_for_llm
)
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select

# 🎯 KONFIGURATION
USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # Prod-User
USE_PRODUCTION_DB = False
TEST_USER_PROMPT = "Ich möchte heute ein intensives Oberkörper-Workout"


async def main():
    """Hauptfunktion für V2 Workout-Generierung Test."""
    print("🏋️ Workout-Generierung V2 Test mit Base Conversation Forking")
    print("=" * 70)
    print(f"👤 User-ID: {USER_ID}")
    print(f"🗄️ Datenbank: {'🚀 Produktionsdatenbank' if USE_PRODUCTION_DB else '💻 Lokale Entwicklungsdatenbank'}")
    print(f"📝 Test-Prompt: {TEST_USER_PROMPT}")
    print("=" * 70)
    
    # Prüfe, ob Base Conversation existiert
    base_conversation_file = Path(__file__).parent / "base_conversation.json"
    if not base_conversation_file.exists():
        print("❌ FEHLER: Keine Base Conversation gefunden!")
        print("💡 Führe zuerst aus: python create_base_conversation.py")
        return
    
    start_time = datetime.now()
    user_id_uuid = UUID(USER_ID)
    
    # Verbinde mit Datenbank
    db_manager = DatabaseManager(use_production=USE_PRODUCTION_DB)
    async with await db_manager.get_session() as db_session:
        try:
            # Lade Trainingsplan
            training_plan_db_obj = await db_session.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
            )
            if not training_plan_db_obj:
                print(f"❌ KEIN TRAININGSPLAN FÜR USER {USER_ID} GEFUNDEN!")
                print("💡 Erstelle einen Trainingsplan für diesen User.")
                return
            
            print(f"✅ Trainingsplan geladen: {training_plan_db_obj}")
            
            # Formatiere Trainingsplan
            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
            
            # Lade Trainingshistorie
            raw_training_history = await get_training_history_for_user_from_db(
                user_id_uuid, db_session, limit=10
            )
            
            print(f"✅ Trainingshistorie geladen: {len(raw_training_history)} Workouts")
            
            # 🚀 NEUE V2 WORKOUT-GENERIERUNG
            print("\n🔄 Starte V2 Workout-Generierung...")
            
            result = await execute_workout_generation_sequence_v2(
                training_plan_str=formatted_training_plan,
                training_history=raw_training_history,
                user_prompt=TEST_USER_PROMPT
            )
            
            # Ergebnis anzeigen
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)
            print("🎉 V2 WORKOUT-GENERIERUNG ERFOLGREICH!")
            print("=" * 70)
            print(f"🏋️ Workout: {result.name}")
            print(f"⏱️ Dauer: {result.duration} min")
            print(f"🎯 Fokus: {result.focus}")
            print(f"📝 Beschreibung: {result.description}")
            print(f"📦 Blöcke: {len(result.blocks)}")
            
            # Blöcke anzeigen
            for i, block in enumerate(result.blocks, 1):
                exercises_count = len(block.exercises)
                print(f"   {i}. {block.name} ({exercises_count} Übungen)")
                
                # Erste paar Übungen anzeigen
                for j, exercise in enumerate(block.exercises[:2], 1):
                    sets_count = len(exercise.sets)
                    print(f"      • {exercise.name} ({sets_count} Sätze)")
                
                if len(block.exercises) > 2:
                    print(f"      • ... und {len(block.exercises) - 2} weitere Übungen")
            
            print(f"\n⏱️ Gesamtdauer: {duration:.1f}s")
            print("=" * 70)
            
            # Zusätzliche Infos
            print("\n💡 VORTEILE DER V2-VERSION:")
            print("• 🏃 Schneller durch Base Conversation Forking")
            print("• 💰 Günstiger durch Token-Caching")
            print("• 📊 Konstante Token-Kosten (keine exponentielle Steigerung)")
            print("• 🔄 Einfache Wartung der Base Conversation")
            
            return result
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    asyncio.run(main()) 