import sys
from pathlib import Path
import asyncio
from datetime import datetime

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

# Imports for DB connection and data loading
from app.llm.utils.db_utils import DatabaseManager # Import the new DatabaseManager
from uuid import UUID
from sqlmodel import select
from app.models.training_plan_model import TrainingPlan
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm, format_training_history_for_llm

# Imports
from app.llm.workout_generation.workout_generation_chain import execute_workout_generation_sequence

# 🎯 KONFIGURATION - Einfach hier ändern!
# USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # Dev-User
USER_ID = "a6a3f5e6-1d4e-4ec2-80c7-ddd257c655a1"  # Prod-User
USE_PRODUCTION_DB = False 
USE_EXERCISE_FILTERING = False  

async def main():
    """Hauptfunktion für Workout-Generation Test mit DB-Verbindung"""
    
    print("🏋️ Workout-Generation Test")
    print(f"🔍 Exercise Filtering: {'✅ Aktiviert' if USE_EXERCISE_FILTERING else '❌ Deaktiviert'}")
    print(f"👤 User-ID: {USER_ID}")
    print(f"🗄️ Datenbank: {'🚀 Produktionsdatenbank' if USE_PRODUCTION_DB else '💻 Lokale Entwicklungsdatenbank'}")
    print("=" * 50)
    
    # Test-Parameter
    user_prompt = ""
    print(f"📝 Test-Prompt: {user_prompt}")
    print()
    
    start_time = datetime.now()
    
    user_id_uuid = UUID(USER_ID)

    db_manager = DatabaseManager(use_production=USE_PRODUCTION_DB) # Instantiate DatabaseManager
    async with await db_manager.get_session() as db_session: # Use async with for session management
        try:
            # Lade Trainingsplan
            training_plan_db_obj = await db_session.scalar(
                select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
            )
            if not training_plan_db_obj:
                print(f"❌ KEIN TRAININGSPLAN FÜR USER {USER_ID} GEFUNDEN. Bitte erstelle einen.")
                return None

            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

            # Lade Trainingshistorie
            raw_training_history = await get_training_history_for_user_from_db(user_id_uuid, db_session, limit=10)
            formatted_history = format_training_history_for_llm(raw_training_history)

            # ✅ Eine Funktion für alles!
            result = await execute_workout_generation_sequence(
                training_plan_obj=training_plan_db_obj,  # Für Exercise Filtering
                training_plan_str=formatted_training_plan,  # Formatierter TrainingPlan String
                training_history=formatted_history,   # Training History
                user_prompt=user_prompt,
                db=db_session,                 # Database Session
                use_exercise_filtering=USE_EXERCISE_FILTERING,
            )
            
            # Ergebnis anzeigen
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("✅ ERFOLGREICH GENERIERT!")
            print("=" * 50)
            print(f"🏋️ Workout: {result.name}")
            print(f"⏱️ Dauer: {result.duration} min")
            print(f"🎯 Fokus: {result.focus}")
            print(f"📦 Blöcke: {len(result.blocks)}")
            
            for i, block in enumerate(result.blocks, 1):
                exercises_count = len(block.exercises)
                print(f"   {i}. {block.name} ({exercises_count} Übungen)")
            
            print(f"\n⏱️ Generierungszeit: {duration:.1f}s")
            print("=" * 50)
            
            return result
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            await db_manager.close() # Close connections when done

if __name__ == "__main__":
    asyncio.run(main())
