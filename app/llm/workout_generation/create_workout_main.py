import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
# Assuming create_workout_main.py is in backend/app/llm/local_execution/
# then backend is 3 levels up.
BACKEND_DIR = Path(__file__).resolve().parents[3]
ROOT_DIR = Path(__file__).resolve().parents[4] # Project root is one level above backend
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Construct .env path relative to the script or a known location if needed
# If .env is in backend, use BACKEND_DIR
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

import asyncio
from app.llm.workout_generation.workout_generation_chain import generate_workout
import json
from datetime import datetime

async def main():
    """
    Test der Superset-Funktionalität ohne Datenbankzugriff
    """
    user_prompt = "Erstelle ein effizientes 30-Minuten HIIT Workout."
    
    print("Starte LLM-Workout-Generierung mit Superset-Anfrage...")
    print(f"User Prompt: {user_prompt}")
    print("-" * 80)
    
    try:
        # Direkter LLM-Call ohne Datenbankzugriff
        llm_output_schema = await generate_workout(
            training_plan=None,  # Keine Trainingsprinzipien
            training_history=None,  # Keine Historie
            user_prompt=user_prompt,
        )
        
        # Konvertiere zu Dictionary
        generated_workout_dict = llm_output_schema.model_dump()
        
        if generated_workout_dict:
            # Save the generated workout dict (raw LLM output) to a JSON file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = ROOT_DIR / f"llm_generated_workout_output_superset_test_{timestamp}.json"
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(generated_workout_dict, f, indent=2, ensure_ascii=False)
                print(f"✅ LLM generated workout output saved to: {file_path}")
                
                print("\n" + "="*80)
                print("GENERIERTES WORKOUT (JSON):")
                print("="*80)
                print(json.dumps(generated_workout_dict, indent=2, ensure_ascii=False))
                
                # Analysiere Supersets
                print("\n" + "="*80)
                print("SUPERSET-ANALYSE:")
                print("="*80)
                analyze_supersets(generated_workout_dict)
                
            except Exception as e:
                print(f"❌ Error saving LLM output to JSON: {e}")
        else:
            print("❌ Workout generation (LLM output) did not return a result.")
            
    except Exception as e:
        print(f"❌ Error during workout generation: {e}")
        import traceback
        traceback.print_exc()

def analyze_supersets(workout_dict):
    """Analysiert das generierte Workout auf Supersets"""
    found_supersets = False
    
    for block in workout_dict.get("blocks", []):
        block_name = block.get("name", "Unnamed Block")
        print(f"\n📋 Block: {block_name}")
        
        superset_groups = {}
        
        for exercise in block.get("exercises", []):
            exercise_name = exercise.get("name", "Unnamed Exercise")
            superset_id = exercise.get("superset_id")
            
            if superset_id:
                found_supersets = True
                if superset_id not in superset_groups:
                    superset_groups[superset_id] = []
                superset_groups[superset_id].append(exercise_name)
                print(f"  💪 {exercise_name} [Superset {superset_id}]")
            else:
                print(f"  💪 {exercise_name} [Normale Übung]")
        
        # Zeige Superset-Gruppierungen
        if superset_groups:
            print(f"\n  🔗 Superset-Gruppierungen in '{block_name}':")
            for superset_id, exercises in superset_groups.items():
                print(f"    Superset {superset_id}: {' ↔ '.join(exercises)}")
    
    if not found_supersets:
        print("⚠️  Keine Supersets gefunden! Das LLM hat möglicherweise die Superset-Anweisung nicht befolgt.")
    else:
        print(f"\n✅ Superset-Funktionalität erfolgreich implementiert!")

if __name__ == "__main__":
    asyncio.run(main())
