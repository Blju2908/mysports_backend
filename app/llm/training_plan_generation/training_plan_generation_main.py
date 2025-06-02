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
from sqlmodel import select
from app.llm.training_plan_generation.training_plan_generation_service import run_training_plan_generation
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel

def write_json_output(plan_schema: TrainingPlanGenerationSchema, filename="training_plan_generation_output.json"):
    """Schreibt das strukturierte Ergebnis in eine JSON-Datei."""
    # Custom JSON encoder to handle date objects
    class DateEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, date):
                return obj.isoformat()
            return super().default(obj)
    
    # Convert Pydantic model to dict and then to JSON
    plan_dict = plan_schema.model_dump()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(plan_dict, f, ensure_ascii=False, indent=2, cls=DateEncoder)

def print_summary(plan_schema: TrainingPlanGenerationSchema):
    """Zeigt eine Zusammenfassung des Trainingsplans im Terminal an."""
    print("\n--- Trainingsplan Zusammenfassung ---")
    
    # Personal Information
    print("📋 PERSÖNLICHE INFORMATIONEN:")
    print(plan_schema.personal_information.content[:200] + "..." if len(plan_schema.personal_information.content) > 200 else plan_schema.personal_information.content)
    
    # Standard Equipment
    print("\n🏋️ STANDARD AUSRÜSTUNG:")
    print(plan_schema.standard_equipment.content[:200] + "..." if len(plan_schema.standard_equipment.content) > 200 else plan_schema.standard_equipment.content)
    
    # Training Principles
    print("\n🎯 TRAININGSPRINZIPIEN:")
    print(plan_schema.training_principles.content[:200] + "..." if len(plan_schema.training_principles.content) > 200 else plan_schema.training_principles.content)
    
    # Training Phases
    print("\n📅 TRAININGSPHASEN:")
    print(plan_schema.training_phases.content[:200] + "..." if len(plan_schema.training_phases.content) > 200 else plan_schema.training_phases.content)
    
    # Remarks
    print("\n📝 BEMERKUNGEN:")
    print(plan_schema.remarks.content[:200] + "..." if len(plan_schema.remarks.content) > 200 else plan_schema.remarks.content)
    
    # Validity info
    print(f"\n⏰ Gültig bis: {plan_schema.valid_until.strftime('%d.%m.%Y')}")

async def create_test_user_and_plan(db: AsyncSession, user_id: UUID):
    """Erstellt einen Test-User und Trainingsplan falls nicht vorhanden"""
    # Check if user exists
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        print(f"🔨 Erstelle Test-User mit ID: {user_id}")
        user = UserModel(id=user_id, onboarding_completed=True)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Check if user has training plan
    if not user.training_plan_id:
        print(f"🔨 Erstelle Trainingsplan für User: {user_id}")
        training_plan = TrainingPlan(
            gender="männlich",
            height=186.0,
            weight=94.0,
            goal_types=["strength", "muscle_building"],
            goal_details="20 Klimmzüge schaffen",
            training_frequency=4,
            session_duration=60,
            experience_level=6,
            fitness_level=6,
            equipment=["gym", "kettlebell"],
            equipment_details="Vollausgestattetes Fitnessstudio + Home Gym",
            include_cardio=False
        )
        db.add(training_plan)
        await db.commit()
        await db.refresh(training_plan)
        
        # Link user to plan
        user.training_plan_id = training_plan.id
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        print(f"✅ Trainingsplan {training_plan.id} mit User {user_id} verknüpft")
    else:
        print(f"✅ User {user_id} hat bereits Trainingsplan {user.training_plan_id}")
    
    return user

async def verify_database_save(db: AsyncSession, user_id: UUID):
    """Überprüft, ob die Daten korrekt in der Datenbank gespeichert wurden"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if user and user.training_plan_id:
        plan_query = select(TrainingPlan).where(TrainingPlan.id == user.training_plan_id)
        plan_result = await db.execute(plan_query)
        training_plan = plan_result.scalar_one_or_none()
        
        if training_plan and training_plan.training_principles_json:
            print("\n🎉 DATENBANK-INTEGRATION ERFOLGREICH!")
            print(f"📊 JSON-Daten gespeichert: {len(str(training_plan.training_principles_json))} Zeichen")
            print(f"📝 Markdown gespeichert: {len(training_plan.training_principles or '')} Zeichen")
            
            # Show JSON structure
            if isinstance(training_plan.training_principles_json, dict):
                print(f"📋 JSON enthält Kategorien: {list(training_plan.training_principles_json.keys())}")
            
            return True
        else:
            print("❌ Keine training_principles_json in der Datenbank gefunden")
            return False
    else:
        print("❌ User oder Trainingsplan nicht gefunden")
        return False

async def main():
    user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff") # Beispiel User ID
    engine = get_engine()
    output_filename = "training_plan_generation_output.json"
    
    async with AsyncSession(engine) as session:
        # 1. Test-User und Trainingsplan erstellen falls nötig
        await create_test_user_and_plan(session, user_id)
        
        # 2. Strukturierten Trainingsplan abrufen
        plan_schema = await run_training_plan_generation(user_id=user_id, db=session)
        
        # 3. Ausgabe im Terminal
        print_summary(plan_schema)
        
        # 4. In JSON-Datei speichern
        write_json_output(plan_schema, filename=output_filename)
        print(f"\n💾 Ergebnis wurde als '{output_filename}' gespeichert.")
        
        # 5. Datenbank-Integration überprüfen
        await verify_database_save(session, user_id)

if __name__ == "__main__":
    asyncio.run(main()) 