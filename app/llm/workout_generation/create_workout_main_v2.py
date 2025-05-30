import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
# Assuming create_workout_main_v2.py is in backend/app/llm/workout_generation/
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
from app.llm.workout_generation.create_workout_service import run_workout_chain_v2
from datetime import datetime

async def main():
    user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff") # Beispiel User ID
    user_prompt = "Bitte gib mir für heute ein HIIT Workout ohne Equipment"

    engine = get_engine()

    async with AsyncSession(engine) as session:
        print("=== Testing v2 Reasoning Chain ===")
        
        # Test v2 reasoning chain
        reasoning_output = await run_workout_chain_v2(
            user_id=user_id, 
            user_prompt=user_prompt, 
            db=session, 
            chain_version="v2"
        )
        
        if reasoning_output:
            # Save the reasoning output to a text file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = ROOT_DIR / f"reasoning_chain_output_{timestamp}.md"
            
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("# Reasoning Chain Output (v2)\n\n")
                    f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write(f"**User Prompt:** {user_prompt}\n\n")
                    f.write("## Generated Workout Text\n\n")
                    f.write(reasoning_output)
                
                print(f"Reasoning chain output saved to: {file_path}")
                print("\n=== First 500 characters of output ===")
                print(reasoning_output[:500] + "..." if len(reasoning_output) > 500 else reasoning_output)
                
            except Exception as e:
                print(f"Error saving reasoning output to file: {e}")
        else:
            print("Reasoning chain did not return a result.")
            
        print("\n=== Testing v1 for comparison ===")
        
        # Test v1 for comparison
        v1_output = await run_workout_chain_v2(
            user_id=user_id, 
            user_prompt=user_prompt, 
            db=session, 
            chain_version="v1"
        )
        
        if v1_output:
            # Save the v1 output for comparison
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path_v1 = ROOT_DIR / f"v1_chain_output_{timestamp}.json"
            
            try:
                with open(file_path_v1, "w", encoding="utf-8") as f:
                    f.write(v1_output)
                
                print(f"v1 chain output saved to: {file_path_v1}")
                print("\n=== First 300 characters of v1 output ===")
                print(v1_output[:300] + "..." if len(v1_output) > 300 else v1_output)
                
            except Exception as e:
                print(f"Error saving v1 output to file: {e}")
        
        print("\n=== Test completed ===")

if __name__ == "__main__":
    # Ensure the script can find the 'app' module if run directly
    # This is handled by the sys.path.append at the top
    asyncio.run(main()) 