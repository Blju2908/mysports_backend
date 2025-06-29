import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import List

# Adjust the sys.path to correctly point to the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.exercise_description.exercise_description_chain import generate_exercise_descriptions_with_batching

def parse_exercise_list_from_file(file_path: Path) -> List[str]:
    """
    Liest eine Liste von Übungsnamen aus einer Textdatei.
    Unterstützt verschiedene Formate (eine Übung pro Zeile, mit/ohne Nummerierung).
    
    Args:
        file_path: Pfad zur Textdatei mit Übungsnamen
        
    Returns:
        Liste der bereinigten Übungsnamen
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        exercise_names = []
        for line in lines:
            # Bereinige die Zeile
            clean_line = line.strip()
            
            # Überspringe leere Zeilen und Kommentare
            if not clean_line or clean_line.startswith('#'):
                continue
            
            # Entferne Nummerierung (z.B. "1. Bankdrücken" -> "Bankdrücken")
            if clean_line[0].isdigit() and '.' in clean_line:
                clean_line = clean_line.split('.', 1)[1].strip()
            
            # Entferne Aufzählungszeichen (z.B. "- Bankdrücken" -> "Bankdrücken")
            if clean_line.startswith('- '):
                clean_line = clean_line[2:].strip()
            elif clean_line.startswith('* '):
                clean_line = clean_line[2:].strip()
            
            if clean_line:
                exercise_names.append(clean_line)
        
        print(f"📋 Parsed {len(exercise_names)} exercises from {file_path}")
        return exercise_names
        
    except Exception as e:
        print(f"❌ Error reading exercise list from {file_path}: {e}")
        raise

async def main():
    """Hauptfunktion des Exercise Description Generators."""
    print("🏋️ Exercise Description Generator")
    print("=" * 50)
    
    # Definiere Input-Datei (sample_exercises.txt als Standard)
    input_file = Path(__file__).parent / "sample_exercises.txt"
    
    # Prüfe ob Input-Datei existiert
    if not input_file.exists():
        print(f"❌ Input file not found: {input_file}")
        print("Please create a text file with exercise names (one per line)")
        return
    
    try:
        # Lade Übungen aus Input-Datei
        exercise_names = parse_exercise_list_from_file(input_file)
        
        if not exercise_names:
            print("❌ No exercises found in input file")
            return
        
        print(f"📊 Total exercises to process: {len(exercise_names)}")
        
        # Konfiguration für Batch-Verarbeitung
        batch_size = 10  # 10 Übungen pro Batch
        delay_between_batches = 2.0  # 2 Sekunden Pause zwischen Batches
        
        estimated_batches = (len(exercise_names) + batch_size - 1) // batch_size
        estimated_time = estimated_batches * (30 + delay_between_batches)  # Geschätzt 30s pro Batch + Pause
        
        print(f"📦 Batch configuration: {batch_size} exercises per batch")
        print(f"📊 Estimated batches: {estimated_batches}")
        print(f"⏱️ Estimated time: {estimated_time/60:.1f} minutes")
        
        # Bestätigung bei größeren Mengen
        if len(exercise_names) > 20:
            confirm = input(f"\nProcess {len(exercise_names)} exercises in {estimated_batches} batches? (y/N): ").strip().lower()
            if confirm not in ['y', 'yes', 'j', 'ja']:
                print("Aborted.")
                return
        
        print(f"\n🚀 Starting exercise description generation...")
        start_time = datetime.now()
        
        # Verarbeite alle Übungen in Batches
        all_exercise_descriptions = await generate_exercise_descriptions_with_batching(
            exercise_names=exercise_names,
            batch_size=batch_size,
            delay_between_batches=delay_between_batches
        )
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Feste Output-Datei
        output_file = Path(__file__).parent / "output" / "exercise_descriptions.json"
        
        print(f"\n{'='*60}")
        print(f"✅ EXERCISE DESCRIPTION GENERATION COMPLETED")
        print(f"{'='*60}")
        print(f"📊 Total new exercises processed: {len(all_exercise_descriptions)}")
        print(f"⏱️ Processing time: {duration.total_seconds():.2f} seconds")
        print(f"💾 Output saved to: {output_file}")
        print(f"{'='*60}")
        
        # Zeige erste Übung als Beispiel
        if all_exercise_descriptions:
            first_exercise = all_exercise_descriptions[0]
            print(f"\n📋 Example: {first_exercise.name_german} ({first_exercise.name_english})")
            print(f"🎯 Target muscles: {', '.join(first_exercise.target_muscle_groups)}")
            print(f"🔧 Equipment options: {', '.join(first_exercise.equipment_options)}")
        elif len(exercise_names) > 0:
            print(f"\n💡 All {len(exercise_names)} exercises already exist in the database/JSON file!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main()) 