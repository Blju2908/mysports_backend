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
import json
from datetime import date
from uuid import UUID
from app.db.session import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from app.llm.service.create_training_principles_service import run_training_principles_chain
from app.llm.schemas.training_principles_schemas import TrainingPrinciplesSchema

def write_json_output(principles_schema: TrainingPrinciplesSchema, filename="training_principles_output.json"):
    """Schreibt das strukturierte Ergebnis in eine JSON-Datei."""
    # Custom JSON encoder to handle date objects
    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, date):
                return obj.isoformat()
            return super().default(obj)
    
    # Convert Pydantic model to dict and then to JSON
    principles_dict = principles_schema.model_dump()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(principles_dict, f, ensure_ascii=False, indent=2, cls=DateEncoder)

def print_summary(principles_schema: TrainingPrinciplesSchema):
    """Zeigt eine Zusammenfassung der Trainingsprinzipien im Terminal an."""
    print("\n--- Trainingsprinzipien Zusammenfassung ---")
    
    # Person overview
    person = principles_schema.person_overview
    print(f"Person: {person.base_data}")
    print(f"Ziele: {person.training_goals}")
    
    # Core principles
    print("\nKernprinzipien:")
    for principle in principles_schema.core_principles:
        print(f"- {principle.name}: {principle.explanation}")
    
    # Training phases summary
    print("\nTrainingsphasen:")
    for phase in principles_schema.training_phases:
        print(f"- {phase.name} ({phase.duration}): {phase.focus}")
    
    # Validity info
    print(f"\nGültig bis: {principles_schema.valid_until}")

async def main():
    user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff") # Beispiel User ID
    engine = get_engine()
    output_filename = "training_principles_output.json"
    
    async with AsyncSession(engine) as session:
        # Strukturierte Trainingsprinzipien abrufen
        principles_schema = await run_training_principles_chain(user_id=user_id, db=session)
        
        # Ausgabe im Terminal
        print_summary(principles_schema)
        
        # In JSON-Datei speichern
        write_json_output(principles_schema, filename=output_filename)
        print(f"\nErgebnis wurde als '{output_filename}' gespeichert.")

if __name__ == "__main__":
    asyncio.run(main()) 