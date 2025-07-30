import sys
from pathlib import Path
from dotenv import load_dotenv
import os



BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))
load_dotenv(os.path.join(BACKEND_DIR, ".env.production"))


if __name__ == "__main__":
    from app.llm.workout_generation_v1.local_work_generation import local_work_generation_main
    api_key = os.getenv("GOOGLE_API_KEY")
    local_work_generation_main(api_key)


    