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
from app.llm.workout_generation.workout_generation_chain import generate_workout_two_step, generate_workout
import json
from datetime import datetime

def get_user_mode():
    """Frage den Nutzer nach dem gewünschten Modus"""
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ['freeform', 'structured', 'two-step']:
            return mode
    
    print("\n🏋️ WORKOUT GENERATION - MODUS AUSWÄHLEN")
    print("=" * 50)
    print("1. 'freeform'    - Nur Schritt 1 (freier Text)")
    print("2. 'two-step'    - Beide Schritte (freier Text + JSON)")
    print("3. 'structured'  - Legacy (direkt JSON, veraltet)")
    print("=" * 50)
    
    while True:
        choice = input("Bitte wähle einen Modus (1-3 oder Namen): ").strip()
        if choice == "1" or choice.lower() == "freeform":
            return "freeform"
        elif choice == "2" or choice.lower() == "two-step":
            return "two-step"
        elif choice == "3" or choice.lower() == "structured":
            return "structured"
        else:
            print("❌ Ungültige Eingabe. Bitte 1, 2, 3 oder den Modus-Namen eingeben.")

async def main():
    print("🏋️ Starte Workout-Generierung...")
    
    # Modus auswählen
    mode = get_user_mode()
    print(f"\n✅ Modus gewählt: {mode.upper()}")
    
    # Beispiel User Prompt
    user_prompt = "Bitte erstelle ein 60 Minuten Push-Workout im Gym mit einem Push-Pull-Legs Split. Ich habe nur Kurzhanteln und Langhanteln."
    
    try:
        # Zeitstempel vor der Erstellung
        start_time = datetime.now()
        timestamp_before = start_time.strftime("%Y%m%d_%H%M%S")
        
        if mode == "freeform":
            print("📝 Starte Freie Workout-Generierung...")
            freeform_text = await generate_workout(
                training_plan=None,
                training_history=None,
                user_prompt=user_prompt,
            )
            result = freeform_text
            
        elif mode == "two-step":
            print("🏋️ Starte Two-Step Workout Generation...")
            print("📝 Schritt 1: Freie Workout-Generierung...")
            structured_workout = await generate_workout_two_step(
                training_plan=None,
                training_history=None,
                user_prompt=user_prompt,
            )
            result = structured_workout
            
        else:  # structured (legacy)
            print("⚠️ Legacy-Modus: Direkte JSON-Generierung (nicht empfohlen)")
            # Hier könnten wir die alte generate_workout mit structured output implementieren
            print("❌ Legacy-Modus noch nicht implementiert")
            return
        
        # Zeitstempel nach der Erstellung
        end_time = datetime.now()
        timestamp_after = end_time.strftime("%Y%m%d_%H%M%S")
        duration = end_time - start_time
        
        if result:
            # Speicherung je nach Modus
            if mode == "freeform":
                file_path = ROOT_DIR / f"llm_generated_workout_freeform_{timestamp_before}.txt"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result)
                
                print(f"\n{'='*60}")
                print(f"✅ FREEFORM WORKOUT GENERIERUNG ERFOLGREICH")
                print(f"{'='*50}")
                print(f"📝 Freies Workout erstellt:")
                print(result)
                print(f"\n📁 Text gespeichert: {file_path}")
                print(f"⏱️ Dauer der Erstellung: {duration.total_seconds():.2f} Sekunden")
                print(f"{'='*60}")
                
            elif mode == "two-step":
                file_path = ROOT_DIR / f"llm_generated_workout_structured_{timestamp_before}.json"
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(result.model_dump_json(indent=2))
                
                print(f"\n{'='*60}")
                print(f"✅ TWO-STEP WORKOUT GENERIERUNG ERFOLGREICH")
                print(f"{'='*50}")
                print(f"🏋️ Workout: {result.name}")
                print(f"⏱️ Dauer: {result.duration} min") 
                print(f"🎯 Fokus: {result.focus}")
                print(f"📦 Blöcke: {len(result.blocks)}")
                
                for i, block in enumerate(result.blocks, 1):
                    print(f"   {i}. {block.name} ({len(block.exercises)} Übungen)")
                
                print(f"\n📁 JSON gespeichert: {file_path}")
                print(f"⏱️ Dauer der Erstellung: {duration.total_seconds():.2f} Sekunden")
                print(f"{'='*60}")
            
        else:
            print("❌ Keine Workout-Daten erhalten")
            
    except Exception as e:
        print(f"❌ Error during workout generation: {e}")
        import traceback
        traceback.print_exc()

# Die Superset-Analyse aus der JSON-Variante entfällt hier –
# sobald Step 2 (Parser) steht, kann sie wieder aktiviert werden.

if __name__ == "__main__":
    asyncio.run(main())
