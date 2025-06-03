import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
# Assuming revise_workout_main.py is in backend/app/llm/local_execution/
# then backend is 3 levels up.
BACKEND_DIR = Path(__file__).resolve().parents[3]
ROOT_DIR = Path(__file__).resolve().parents[4]  # Project root is one level above backend
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Construct .env path relative to the script or a known location if needed
# If .env is in backend, use BACKEND_DIR
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

import asyncio
import json
from datetime import datetime
from app.llm.workout_revision.workout_revision_chain import revise_workout


async def main():
    """
    Test der Superset-Funktionalität in workout_revision ohne Datenbankzugriff
    """
    
    # Beispiel-Workout zum Überarbeiten
    existing_workout = {
        "id": 123,
        "name": "Standard Push Training",
        "description": "Grundlegendes Push-Workout",
        "duration": 60,
        "focus": "Brust, Schultern, Trizeps",
        "blocks": [
            {
                "id": 1,
                "name": "Hauptteil",
                "description": "Krafttraining",
                "exercises": [
                    {
                        "id": 1,
                        "name": "Bankdrücken",
                        "description": "Klassisches Bankdrücken",
                        "superset_id": None,
                        "sets": [
                            {"values": [80, 10, None, None, 90]},
                            {"values": [80, 8, None, None, 90]},
                            {"values": [80, 6, None, None, 90]}
                        ]
                    },
                    {
                        "id": 2,
                        "name": "Schulterdrücken",
                        "description": "Schulterdrücken mit Kurzhanteln",
                        "superset_id": None,
                        "sets": [
                            {"values": [20, 12, None, None, 90]},
                            {"values": [20, 10, None, None, 90]},
                            {"values": [20, 8, None, None, 90]}
                        ]
                    },
                    {
                        "id": 3,
                        "name": "Trizeps Dips",
                        "description": "Dips am Barren",
                        "superset_id": None,
                        "sets": [
                            {"values": [None, 12, None, None, 60]},
                            {"values": [None, 10, None, None, 60]},
                            {"values": [None, 8, None, None, 60]}
                        ]
                    }
                ]
            }
        ]
    }
    
    # Test-Feedback für Superset-Erstellung
    user_feedback = "Erstelle Supersets aus Bankdrücken und Trizeps Dips, damit das Training effizienter wird. Außerdem mache das Workout kürzer - 45 Minuten."
    
    print("🔄 Starte Workout-Revision mit Superset-Anfrage...")
    print(f"User Feedback: {user_feedback}")
    print("-" * 80)
    
    try:
        # Direkter LLM-Call für Revision
        revised_workout_schema = await revise_workout(
            existing_workout=existing_workout,
            user_feedback=user_feedback,
            training_plan=None,
            training_history=None
        )
        
        # Konvertiere zu Dictionary
        revised_workout_dict = revised_workout_schema.model_dump()
        
        if revised_workout_dict:
            # Save the revised workout to a JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = ROOT_DIR / f"llm_revised_workout_superset_test_{timestamp}.json"
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(revised_workout_dict, f, indent=2, ensure_ascii=False)
                print(f"✅ Revised workout saved to: {file_path}")
                
                print("\n" + "="*80)
                print("ORIGINAL WORKOUT:")
                print("="*80)
                print(json.dumps(existing_workout, indent=2, ensure_ascii=False))
                
                print("\n" + "="*80)
                print("REVISED WORKOUT (JSON):")
                print("="*80)
                print(json.dumps(revised_workout_dict, indent=2, ensure_ascii=False))
                
                # Analysiere Superset-Änderungen
                print("\n" + "="*80)
                print("SUPERSET-ANALYSE:")
                print("="*80)
                analyze_superset_changes(existing_workout, revised_workout_dict)
                
            except Exception as e:
                print(f"❌ Error saving revised workout: {e}")
        else:
            print("❌ Workout revision did not return a result.")
            
    except Exception as e:
        print(f"❌ Error during workout revision: {e}")
        import traceback
        traceback.print_exc()

def analyze_superset_changes(original_workout, revised_workout):
    """Analysiert die Superset-Änderungen zwischen Original und revidiertem Workout"""
    
    print("🔍 Vergleiche Original vs. Revidiert:")
    
    # Original Supersets analysieren
    original_supersets = extract_supersets(original_workout)
    revised_supersets = extract_supersets(revised_workout)
    
    print(f"\n📊 Original Workout:")
    print(f"   - Name: {original_workout.get('name')}")
    print(f"   - Dauer: {original_workout.get('duration')} Minuten")
    if original_supersets:
        print(f"   - Supersets: {len(original_supersets)}")
        for superset_id, exercises in original_supersets.items():
            print(f"     • {superset_id}: {' ↔ '.join(exercises)}")
    else:
        print(f"   - Supersets: Keine")
    
    print(f"\n📊 Revidiertes Workout:")
    print(f"   - Name: {revised_workout.get('name')}")
    print(f"   - Dauer: {revised_workout.get('duration')} Minuten")
    if revised_supersets:
        print(f"   - Supersets: {len(revised_supersets)}")
        for superset_id, exercises in revised_supersets.items():
            print(f"     • {superset_id}: {' ↔ '.join(exercises)}")
    else:
        print(f"   - Supersets: Keine")
    
    # Änderungen bewerten
    if not original_supersets and revised_supersets:
        print(f"\n✅ Neue Supersets erfolgreich erstellt!")
    elif original_supersets and not revised_supersets:
        print(f"\n⚠️  Supersets wurden entfernt!")
    elif original_supersets != revised_supersets:
        print(f"\n🔄 Supersets wurden geändert!")
    else:
        print(f"\n➡️  Keine Superset-Änderungen")

def extract_supersets(workout_dict):
    """Extrahiert alle Supersets aus einem Workout"""
    supersets = {}
    
    for block in workout_dict.get("blocks", []):
        for exercise in block.get("exercises", []):
            superset_id = exercise.get("superset_id")
            if superset_id:
                if superset_id not in supersets:
                    supersets[superset_id] = []
                supersets[superset_id].append(exercise.get("name", "Unnamed Exercise"))
    
    return supersets

if __name__ == "__main__":
    asyncio.run(main()) 