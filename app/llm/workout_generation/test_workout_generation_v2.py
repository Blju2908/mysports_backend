#!/usr/bin/env python3
"""
Test script for the streamlined V2 workout generation.
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv

# 🎯 KONFIGURATION
USER_ID_DEV = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # Prod-User
USER_ID_PROD = "a6a3f5e6-1d4e-4ec2-80c7-ddd257c655a1"
USE_PRODUCTION_DB = True
TEST_USER_PROMPT = ""
GENERATION_MODE = "one-step" # Can be "one-step" or "two-step"

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
if USE_PRODUCTION_DB:
    print("🔌 Loading .env.production...")
    load_dotenv(dotenv_path=BACKEND_DIR / ".env.production", override=True)
else:
    print("🔌 Loading .env.development...")
    load_dotenv(dotenv_path=BACKEND_DIR / ".env.development", override=True)

# Imports
from app.llm.utils.db_utils import DatabaseManager
from app.llm.workout_generation.workout_generation_chain_v2 import execute_workout_generation_sequence_v2
from app.llm.workout_generation.create_workout_service import (
    format_training_plan_for_llm
)
from app.llm.workout_generation.create_workout_schemas import CompactWorkoutSchema, WorkoutSchema
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select


async def main():
    """Hauptfunktion für V2 Workout-Generierung Test."""
    print("🏋️ Streamlined Workout Generation V2 Test")
    print("=" * 70)
    print(f"👤 User-ID: {USER_ID_DEV}")
    print(f"🗄️ Datenbank: {'🚀 Produktionsdatenbank' if USE_PRODUCTION_DB else '💻 Lokale Entwicklungsdatenbank'}")
    print(f"📝 Test-Prompt: {TEST_USER_PROMPT}")
    print(f"⚙️ Generation Mode: {GENERATION_MODE}")
    print("=" * 70)

    start_time = datetime.now()
    
    if USE_PRODUCTION_DB:
        user_id_uuid = UUID(USER_ID_PROD)
    else:
        user_id_uuid = UUID(USER_ID_DEV)
    
    # Verbinde mit Datenbank
    db_manager = DatabaseManager(use_production=USE_PRODUCTION_DB)
    async with await db_manager.get_session() as db_session:
        try:
            # Lade Trainingsplan
            training_plan_db_obj = await db_session.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
            )
            if not training_plan_db_obj:
                print(f"❌ KEIN TRAININGSPLAN FÜR USER {user_id_uuid} GEFUNDEN!")
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
                user_prompt=TEST_USER_PROMPT,
                generation_mode=GENERATION_MODE,
                db_manager=db_manager # Pass db_manager instead of db_session
            )
            
            # Ergebnis anzeigen
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)

            if isinstance(result, str):
                print("🎉 V2 FREEFORM WORKOUT GENERIERUNG ERFOLGREICH!")
                print("=" * 70)
                print("--- FREEFORM WORKOUT TEXT ---")
                print(result)
                print("-----------------------------")
            elif isinstance(result, CompactWorkoutSchema):
                print("🎉 V2 ONE-STEP (COMPACT) WORKOUT-GENERIERUNG ERFOLGREICH!")
                print("=" * 70)
                print(result.model_dump_json(indent=2))

            elif isinstance(result, WorkoutSchema):
                print("🎉 V2 TWO-STEP (VERBOSE) WORKOUT-GENERIERUNG ERFOLGREICH!")
                print("=" * 70)
                print(f"🏋️ Workout: {result.name}")
                print(f"⏱️ Dauer: {result.duration} min")
                print(f"🎯 Fokus: {result.focus}")
                print(f"📝 Beschreibung: {result.description}")
                print(f"📦 Blöcke: {len(result.blocks)}")
                for i, block in enumerate(result.blocks, 1):
                    print(f"   {i}. {block.name} ({len(block.exercises)} Übungen)")

            else:
                print(f"🤔 Unbekannter Ergebnistyp: {type(result)}")

            print(f"\n⏱️ Gesamtdauer: {duration:.1f}s")
            print("=" * 70)
            
            return result
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    asyncio.run(main()) 