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
from uuid import UUID
from app.db.session import get_engine # app. is now resolvable due to sys.path modification
from sqlmodel.ext.asyncio.session import AsyncSession
from app.llm.service.create_workout_service import run_workout_chain
import json
from datetime import datetime

async def main():
    user_id = UUID("e505cc55-a07a-4bd1-816d-b56611308b15") # Beispiel User ID
    user_prompt = "Heute würde ich gerne Mal eine HIIT Einheit mit eine Kettlebell machen."

    engine = get_engine()

    async with AsyncSession(engine) as session:
        # Run workout chain, save_to_db=False to get the raw LLM output dict
        generated_workout_llm_output_dict = await run_workout_chain(
            user_id=user_id, 
            user_prompt=user_prompt, 
            db=session, 
            save_to_db=True
        )
        
        if generated_workout_llm_output_dict:
            # Save the generated workout dict (raw LLM output) to a JSON file
            # in the project's root directory.
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            # Use ROOT_DIR for the output path
            file_path = ROOT_DIR / f"llm_generated_workout_output_{timestamp}.json"
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(generated_workout_llm_output_dict, f, indent=2, ensure_ascii=False)
                print(f"LLM generated workout output saved to: {file_path}")
            except Exception as e:
                print(f"Error saving LLM output to JSON: {e}")
        else:
            print("Workout generation (LLM output) did not return a result.")

if __name__ == "__main__":
    # Ensure the script can find the 'app' module if run directly
    # This is handled by the sys.path.append at the top
    asyncio.run(main())
