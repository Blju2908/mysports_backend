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
import json
from typing import Any, Dict

# 🎯 KONFIGURATION
USER_ID_DEV = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # Prod-User
USER_ID_PROD = "a6a3f5e6-1d4e-4ec2-80c7-ddd257c655a1"
USE_PRODUCTION_DB = False
TEST_USER_PROMPT = ""

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
from app.llm.workout_generation.workout_generation_chain_v2 import (
    execute_workout_generation_sequence_v2,
)
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm
from app.llm.workout_generation.create_workout_schemas import (
    CompactWorkoutSchema,
)
from app.llm.workout_generation.workout_parser import (
    parse_compact_workout_to_db_models
)
from app.services.workout_service import get_latest_workouts_with_details
from app.llm.workout_generation.exercise_filtering_service import get_all_exercises_for_prompt
from app.llm.workout_generation.workout_utils import summarize_training_history
from app.models.training_plan_model import TrainingPlan
from app.models.workout_model import Workout
from sqlmodel import select

def document_output(stage_name: str, data: Any, out_dir: Path):
    """Saves the given data to a file in the specified output directory."""
    ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    output_path = out_dir / f"{ts}_{stage_name}.json"

    if hasattr(data, "model_dump_json"):
        output_text = data.model_dump_json(indent=2)
    elif isinstance(data, dict):
        output_text = json.dumps(data, indent=2, ensure_ascii=False)
    else:
        # Fallback for other types
        output_text = str(data)

    output_path.write_text(output_text, encoding="utf-8")
    print(f"📝 Dokumentiert: {output_path.name}")

def serialize_workout_for_doc(workout: Workout) -> Dict:
    """Converts a Workout SQLModel object to a serializable dictionary for documentation."""
    return {
        "name": workout.name,
        "description": workout.description,
        "focus": workout.focus,
        "duration": workout.duration,
        "notes": workout.notes,
        "muscle_group_load": workout.muscle_group_load,
        "focus_derivation": workout.focus_derivation,
        "blocks": [
            {
                "name": block.name,
                "description": block.description,
                "position": block.position,
                "exercises": [
                    {
                        "name": ex.name,
                        "superset_id": ex.superset_id,
                        "position": ex.position,
                        "sets": [
                            {
                                "reps": s.reps,
                                "weight": s.weight,
                                "duration": s.duration,
                                "distance": s.distance,
                                "rest_time": s.rest_time,
                                "position": s.position,
                            } for s in ex.sets
                        ],
                    } for ex in block.exercises
                ],
            } for block in workout.blocks
        ],
    }

async def main():
    """Hauptfunktion für V2 Workout-Generierung Test."""
    print("🏋️ Streamlined Workout Generation V2 Test")
    print("=" * 70)
    print(f"👤 User-ID: {USER_ID_DEV}")
    print(f"🗄️ Datenbank: {'🚀 Produktionsdatenbank' if USE_PRODUCTION_DB else '💻 Lokale Entwicklungsdatenbank'}")
    print(f"📝 Test-Prompt: {TEST_USER_PROMPT}")
    print("=" * 70)

    # Setup output directory for this run
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)
    
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

            training_plan_id = training_plan_db_obj.id
            print(f"✅ Trainingsplan geladen: {training_plan_id=}")

            # Formatiere Trainingsplan
            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

            # Lade Trainingshistorie
            raw_training_history = await get_latest_workouts_with_details(
                db=db_session, user_id=user_id_uuid, number_of_workouts=10
            )
            
            print(f"✅ Trainingshistorie geladen: {len(raw_training_history)} Workouts")
            
            # Summarize training history before calling the chain
            summarized_history_str = summarize_training_history(raw_training_history)
            print("✅ Trainingshistorie zusammengefasst.")

            # Load exercise library
            print("🔄 Loading all exercises from database...")
            exercise_library_str = await get_all_exercises_for_prompt(db_session)
            print(f"✅ Loaded {len(exercise_library_str.splitlines())} exercises from database.")


            # 🚀 NEUE V2 WORKOUT-GENERIERUNG
            print("\n🔄 Starte V2 Workout-Generierung...")
            
            llm_result = await execute_workout_generation_sequence_v2(
                training_plan_str=formatted_training_plan,
                training_history_str=summarized_history_str, # Pass summarized string
                user_prompt=TEST_USER_PROMPT,
                exercise_library_str=exercise_library_str,
            )
            
            # Ergebnis anzeigen und dokumentieren
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print("\n" + "=" * 70)

            if isinstance(llm_result, CompactWorkoutSchema):
                print("🎉 V2 ONE-STEP (COMPACT) WORKOUT-GENERIERUNG ERFOLGREICH!")
                document_output("llm_raw_output", llm_result, out_dir)

                print("\n🔄 Starte Parsing in DB-Modelle...")
                parsed_workout = parse_compact_workout_to_db_models(
                    compact_workout=llm_result,
                    user_id=user_id_uuid,
                    training_plan_id=training_plan_id,
                )
                print("✅ Parsing erfolgreich!")
                
                # Document the parsed workout
                serialized_workout = serialize_workout_for_doc(parsed_workout)
                document_output("parsed_db_model_workout", serialized_workout, out_dir)
                
                # Speichere das Workout in der Datenbank
                # print("\n🔄 Speichere das Workout in der Datenbank...")
                # saved_workout = await save_workout_to_db(parsed_workout, db_session)
                # print(f"✅ Workout erfolgreich gespeichert mit ID: {saved_workout.id}")


            else:
                print(f"🤔 Unbekannter Ergebnistyp: {type(llm_result)}")
                document_output("unknown_output", llm_result, out_dir)

            print(f"\n⏱️ Gesamtdauer: {duration:.1f}s")
            print("=" * 70)
            
            return llm_result
            
        except Exception as e:
            print(f"❌ FEHLER: {e}")
            import traceback
            traceback.print_exc()
            return None


if __name__ == "__main__":
    asyncio.run(main()) 