import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
import os

from dotenv import load_dotenv

dotenv_path = "/Users/julianblochl/Programmieren/mysports/backend/.env"
load_dotenv(dotenv_path=dotenv_path)

import asyncio
from uuid import UUID
from app.db.session import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from backend.app.llm.service.create_workout_service import run_workout_chain


async def main():
    user_id = UUID("a6a3f5e6-1d4e-4ec2-80c7-ddd257c655a1")
    user_prompt = "Bitte ein knackiges Oberkörper-Workout!"

    # Get engine
    engine = get_engine()

    async with AsyncSession(engine) as session:
        # Run workout chain
        await run_workout_chain(
            user_id=user_id, user_prompt=user_prompt, db=session, save_to_db=True
        )
        


if __name__ == "__main__":
    asyncio.run(main())
