import sys
from pathlib import Path

# Adjust the sys.path to correctly point to the backend directory
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

def test_imports():
    """Test if all imports for workout revision work correctly."""
    try:
        print("Testing imports...")
        
        # Test chain import
        print("1. Testing workout_revision_chain import...")
        from app.llm.chains.workout_revision_chain import revise_workout
        print("   ✓ workout_revision_chain imported successfully")
        
        # Test service import
        print("2. Testing workout_revision_service import...")
        from app.llm.service.workout_revision_service import (
            run_workout_revision_chain, 
            get_workout_for_revision,
            workout_to_dict
        )
        print("   ✓ workout_revision_service imported successfully")
        
        # Test other dependencies
        print("3. Testing other dependencies...")
        from app.services.workout_service import get_workout_details
        from app.llm.schemas.create_workout_schemas import WorkoutSchema
        from app.models.workout_model import Workout
        from app.models.set_model import Set, SetStatus
        print("   ✓ All dependencies imported successfully")
        
        print("\n🎉 All imports successful! The workout revision system is ready to use.")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_imports() 