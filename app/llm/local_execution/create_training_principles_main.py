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
from app.llm.service.create_training_principles_service import run_training_principles_chain

def write_markdown(result, filename="training_principles_output.md"):
    lines = ["# Trainingsprinzipien\n"]
    for principle in result.principles:
        lines.append(f"- **{principle.name}**: {principle.description}")
    lines.append("\n## Zusammenfassung\n")
    lines.append(result.summary)
    with open(filename, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

async def main():
    user_id = UUID("51d17983-1c62-494f-bd0c-20503c200605")
    engine = get_engine()
    async with AsyncSession(engine) as session:
        result = await run_training_principles_chain(user_id=user_id, db=session)
        print("\n--- Trainingsprinzipien ---")
        for principle in result.principles:
            print(f"- {principle.name}: {principle.description}")
        print("\nZusammenfassung:")
        print(result.summary)
        write_markdown(result)
        print("\nErgebnis wurde als 'training_principles_output.md' gespeichert.")

if __name__ == "__main__":
    asyncio.run(main()) 