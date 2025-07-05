"""
Step 1: Download Exercise Descriptions from Database

Exportiert alle Übungsbeschreibungen aus der Datenbank in eine JSON-Datei
für die weitere Verarbeitung mit LLM.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any
from sqlmodel import select

from app.llm.utils.db_utils import create_db_session
from app.models.exercise_description_model import ExerciseDescription


async def download_exercises_to_json(
    use_production: bool = False,
    output_file: str = None
) -> str:
    """
    Lädt alle Übungsbeschreibungen aus der Datenbank und speichert sie als JSON.
    
    Args:
        use_production: True für Produktions-DB, False für Entwicklungs-DB
        output_file: Pfad zur Ausgabedatei (optional)
        
    Returns:
        Pfad zur erstellten JSON-Datei
    """
    
    # Output-Datei bestimmen
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"exercise_descriptions_{timestamp}.json"
    
    output_path = Path(__file__).parent / "output" / output_file
    output_path.parent.mkdir(exist_ok=True)
    
    print(f"📥 Lade Übungsbeschreibungen aus {'Produktions' if use_production else 'Entwicklungs'}-Datenbank...")
    
    exercises_data = []
    
    async for session in create_db_session(use_production=use_production):
        # Alle Übungen laden
        stmt = select(ExerciseDescription).order_by(ExerciseDescription.name_german)
        result = await session.execute(stmt)
        exercises = result.scalars().all()
        
        print(f"📊 Gefunden: {len(exercises)} Übungsbeschreibungen")
        
        # Konvertierung zu Dictionary für JSON-Serialisierung
        for exercise in exercises:
            exercise_dict = {
                "name_german": exercise.name_german,
                "name_english": exercise.name_english,
                "description_german": exercise.description_german,
                "difficulty_level": exercise.difficulty_level,
                "primary_movement_pattern": exercise.primary_movement_pattern,
                "is_unilateral": exercise.is_unilateral,
                "equipment_options": exercise.equipment_options,
                "target_muscle_groups": exercise.target_muscle_groups,
                "execution_steps": exercise.execution_steps,
                # Aktuelle Attribut-Werte (falls schon vorhanden)
                "requires_repetitions": exercise.requires_repetitions,
                "requires_weight": exercise.requires_weight,
                "requires_duration": exercise.requires_duration,
                "requires_distance": exercise.requires_distance,
                "requires_rest": exercise.requires_rest,
                "created_at": exercise.created_at.isoformat(),
                "updated_at": exercise.updated_at.isoformat(),
            }
            exercises_data.append(exercise_dict)
        
        break  # Wichtig: break nach Operationen
    
    # JSON-Datei speichern
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(exercises_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Übungsbeschreibungen gespeichert: {output_path}")
    print(f"📄 Datei-Größe: {output_path.stat().st_size / 1024:.1f} KB")
    
    return str(output_path)


async def main():
    """
    Hauptfunktion für direkten Aufruf des Skripts.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Download exercise descriptions from database")
    parser.add_argument(
        "--production", 
        action="store_true", 
        help="Use production database instead of development"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        help="Output filename (default: exercise_descriptions_TIMESTAMP.json)"
    )
    
    args = parser.parse_args()
    
    try:
        output_file = await download_exercises_to_json(
            use_production=args.production,
            output_file=args.output
        )
        print(f"\n🎉 Download erfolgreich abgeschlossen!")
        print(f"📁 Datei: {output_file}")
        
    except Exception as e:
        print(f"❌ Fehler beim Download: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main()) 