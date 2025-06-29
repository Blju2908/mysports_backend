import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
BACKEND_DIR = Path(__file__).resolve().parent
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Load production environment
dotenv_path = BACKEND_DIR / ".env.production"
load_dotenv(dotenv_path=dotenv_path)

import asyncio
from app.llm.utils.db_utils import test_database_connection, create_db_session
from sqlmodel import select, text

async def test_production_db():
    """Test der Produktionsdatenbank-Verbindung und Workout-Suche."""
    
    print("=" * 60)
    print("🧪 DATENBANK-VERBINDUNGSTEST")
    print("=" * 60)
    
    # 1. Basis-Verbindungstest
    connection_ok = await test_database_connection(use_production=True)
    
    if not connection_ok:
        print("❌ Basis-Verbindung fehlgeschlagen!")
        return
    
    # 2. Workout-Tabelle testen
    try:
        print("\n🔍 Teste Workout-Tabelle...")
        
        async for session in create_db_session(use_production=True):
            # Zähle alle Workouts
            result = await session.execute(text("SELECT COUNT(*) FROM workouts"))
            workout_count = result.scalar()
            print(f"📊 Anzahl Workouts in Datenbank: {workout_count}")
            
            # Suche Workout 417
            result = await session.execute(text("SELECT id, name FROM workouts WHERE id = 417"))
            workout_417 = result.first()
            
            if workout_417:
                print(f"✅ Workout 417 gefunden: {workout_417[1]}")
            else:
                print("❌ Workout 417 nicht gefunden!")
                
                # Zeige die letzten 10 Workouts
                print("\n🔍 Letzte 10 Workouts in der Datenbank:")
                result = await session.execute(text("SELECT id, name FROM workouts ORDER BY id DESC LIMIT 10"))
                recent_workouts = result.fetchall()
                
                for workout in recent_workouts:
                    print(f"   ID: {workout[0]} - Name: {workout[1]}")
            
            break
            
    except Exception as e:
        print(f"❌ Fehler bei Workout-Test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_production_db()) 