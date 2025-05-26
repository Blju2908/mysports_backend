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
from app.db.session import get_engine  # app. is now resolvable due to sys.path modification
from sqlmodel.ext.asyncio.session import AsyncSession
from app.llm.service.workout_revision_service import run_workout_revision_chain, get_workout_for_revision
import json
from datetime import datetime


async def main():
    # ===== KONFIGURATION =====
    # Hier die ID des zu überarbeitenden Workouts eintragen
    workout_id = 1  # Beispiel: ID des Workouts, das überarbeitet werden soll
    
    # Hier das User-Feedback eintragen
    user_feedback = "Ich möchte nur Übungen mit Kurzhanteln machen."
    
    # Optional: Zusätzlicher Kontext
    training_plan = ""  # Optional: Trainingsplan als String
    training_history = ""  # Optional: Trainingshistorie als JSON-String
    # ==========================

    engine = get_engine()

    async with AsyncSession(engine) as session:
        try:
            print(f"Loading existing workout with ID: {workout_id}")
            print(f"User Feedback: {user_feedback}")
            print("=" * 50)
            
            # 2. Führe die Workout-Revision aus
            print("Starting workout revision...")
            revised_workout_schema = await run_workout_revision_chain(
                workout_id=workout_id,
                user_feedback=user_feedback,
                training_plan=training_plan,
                training_history=training_history,
                db=session
            )
            
            if revised_workout_schema:
                # Convert Pydantic model to dict for JSON serialization
                revised_workout_dict = revised_workout_schema.model_dump()
                
                print("=== ÜBERARBEITETES WORKOUT ===")
                print(json.dumps(revised_workout_dict, indent=2, ensure_ascii=False, default=str))
                
                # Save the revised workout to a JSON file in the project's root directory
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_path = ROOT_DIR / f"revised_workout_output_{timestamp}.json"
                
                # Create output data with context
                output_data = {
                    "original_workout_id": workout_id,
                    "user_feedback": user_feedback,
                    "revision_timestamp": datetime.now().isoformat(),
                    "revised_workout": revised_workout_dict
                }
                
                try:
                    with open(file_path, "w", encoding="utf-8") as f:
                        json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
                    print(f"\nRevised workout saved to: {file_path}")
                except Exception as e:
                    print(f"Error saving revised workout to JSON: {e}")
            else:
                print("Workout revision did not return a result.")
                
        except Exception as e:
            print(f"Error during workout revision: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 