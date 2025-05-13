import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
import os
from dotenv import load_dotenv

# Sicherstellen, dass der Pfad zur .env-Datei korrekt ist.
# Der Pfad sollte relativ zum aktuellen Skript oder absolut sein.
# Beispiel: Wenn .env.development im backend-Verzeichnis liegt und dieses Skript in backend/app/llm/local_execution/
dotenv_path = Path(__file__).resolve().parents[3] / '.env.development'
load_dotenv(dotenv_path=dotenv_path)

import asyncio
from uuid import UUID
from app.db.session import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.llm.service.create_training_principles_service import run_training_principles_chain

def write_markdown(result_text: str, filename="training_principles_output.md"):
    """Schreibt den Ergebnis-Text direkt in eine Markdown-Datei."""
    # Der Titel kann hier oder im Prompt selbst definiert sein.
    # Wenn im Prompt, dann kann diese Zeile entfernt werden.
    # lines = ["# Trainingsprinzipien und -philosophie\n"]
    # lines.append(result_text)
    with open(filename, "w", encoding="utf-8") as f:
        # f.write("\n".join(lines))
        f.write(result_text) # Direkter Text wird geschrieben

async def main():
    user_id = UUID("e505cc55-a07a-4bd1-816d-b56611308b15") # Beispiel User ID
    engine = get_engine()
    output_filename = "training_principles_output.md"
    async with AsyncSession(engine) as session:
        # run_training_principles_chain gibt jetzt direkt den String zurück
        result_text = await run_training_principles_chain(user_id=user_id, db=session)
        
        print("\n--- Trainingsprinzipien und -philosophie (Text Output) ---")
        print(result_text)
        
        write_markdown(result_text, filename=output_filename)
        print(f"\nErgebnis wurde als '{output_filename}' gespeichert.")

if __name__ == "__main__":
    asyncio.run(main()) 