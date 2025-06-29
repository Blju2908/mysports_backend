import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
ROOT_DIR = Path(__file__).resolve().parents[4] # Project root is one level above backend
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# ============================================================
# KONFIGURATION - HIER ANPASSEN
# ============================================================

# User-ID (UUID) - Ersetze mit deiner echten User-ID
USER_ID = "a6a3f5e6-1d4e-4ec2-80c7-ddd257c655a1"  # Als String für einfachere Konfiguration

# Workout-ID (int) - Ersetze mit der ID des Workouts, das analysiert werden soll
WORKOUT_ID = 420  # <-- HIER DEINE WORKOUT-ID EINTRAGEN

# Datenbankwahl - True für Produktionsdatenbank, False für lokale DB
USE_PRODUCTION_DB = True  # <-- HIER ANPASSEN

# ============================================================

# Lade die richtige Umgebungskonfiguration basierend auf der Datenbankwahl
if USE_PRODUCTION_DB:
    dotenv_path = BACKEND_DIR / ".env.production"
    print(f"🔧 Lade Produktions-Umgebung: {dotenv_path}")
else:
    dotenv_path = BACKEND_DIR / ".env.development"
    print(f"🔧 Lade Entwicklungs-Umgebung: {dotenv_path}")

load_dotenv(dotenv_path=dotenv_path)

import asyncio
from app.llm.workout_rationale.workout_rationale_service import generate_workout_rationale
from datetime import datetime
from uuid import UUID

async def main():
    """
    Hauptfunktion für die Workout-Rationale-Generierung.
    
    Konfiguriere die drei Variablen oben und führe das Script aus.
    Das System generiert eine sportwissenschaftliche Begründung für das spezifische Workout
    und speichert sowohl den verwendeten Prompt als auch die finale Analyse im output-Ordner.
    """
    
    start_time = datetime.now()
    
    # Konvertiere User-ID zu UUID
    user_id_uuid = UUID(USER_ID)
    
    print("🧬 Starte sportwissenschaftliche Workout-Analyse...")
    print(f"👤 User-ID: {user_id_uuid}")
    print(f"🏋️ Workout-ID: {WORKOUT_ID}")
    print(f"🗄️ Datenbank: {'🚀 Produktionsdatenbank' if USE_PRODUCTION_DB else '💻 Lokale Entwicklungsdatenbank'}")
    print()
    
    try:
        print("📚 Lade Workout-Daten, Trainingsziele und Trainingshistorie...")
        print("🧬 Generiere wissenschaftlich fundierte Analyse...")
        
        # Generiere die sportwissenschaftliche Begründung
        rationale_text = await generate_workout_rationale(
            user_id=user_id_uuid,
            workout_id=WORKOUT_ID,
            use_production_db=USE_PRODUCTION_DB
        )
        
        # Berechne Ausführungszeit
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print()
        print("=" * 80)
        print("✅ SPORTWISSENSCHAFTLICHE ANALYSE ERFOLGREICH GENERIERT")
        print("=" * 80)
        print(f"👤 User: {user_id_uuid}")
        print(f"🏋️ Workout: {WORKOUT_ID}")
        print("🧬 Wissenschaftliche Begründung erstellt:")
        print("-" * 80)
        print(rationale_text)
        print("-" * 80)
        print()
        print("📁 Prompt und Analyse wurden im output-Ordner gespeichert:")
        print("   - Prompt: app/llm/workout_rationale/output/prompt_user_*_workout_*_*.md")
        print("   - Analyse: app/llm/workout_rationale/output/rationale_user_*_workout_*_*.txt")
        print(f"⏱️ Ausführungsdauer: {duration:.2f} Sekunden")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Fehler bei der Analyse-Generierung: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 