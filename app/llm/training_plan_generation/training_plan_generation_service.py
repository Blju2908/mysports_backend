from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.trainingplan_db_access import get_training_plan_for_user
from app.llm.training_plan_generation.training_plan_generation_chain import generate_training_plan_generation
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema
from app.models.training_plan_model import TrainingPlan
import json
from datetime import date

class DateEncoder(json.JSONEncoder):
    """JSON-Encoder, der date-Objekte automatisch in ISO-Format-Strings umwandelt."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

async def run_training_plan_generation(
    user_id: UUID | None,
    db: AsyncSession
) -> TrainingPlanGenerationSchema:
    """
    Lädt die Trainingsziele des Nutzers und leitet daraus einen strukturierten 
    Trainingsplan mit 5 bearbeitbaren Kategorien ab.

    Args:
        user_id: Die ID des Benutzers
        db: Die Datenbankverbindung

    Returns:
        Der strukturierte Trainingsplan als TrainingPlanGenerationSchema
    """
    # 1. Trainingsplan laden (falls user_id vorhanden)
    training_plan = None
    if user_id is not None:
        training_plan = await get_training_plan_for_user(user_id, db)
        # Remove the column training_principles_json from the plan
        training_plan.training_principles_json = None
        training_plan.training_principles = ""
        if training_plan is None:
            raise ValueError("Kein Trainingsplan für den Nutzer gefunden.")
    
    # 2. Daten für LLM-Anfrage vorbereiten
    training_goals = None
    if training_plan is not None:
        training_goals = training_plan.model_dump()

    # 3. LLM-Call durchführen
    plan_schema = await generate_training_plan_generation(training_goals)
    
    # 4. Wenn user_id vorhanden, Ergebnisse in Datenbank speichern
    if user_id is not None and training_plan is not None:
        await save_plan_to_db(training_plan, plan_schema, db)
    
    return plan_schema

async def save_plan_to_db(
    training_plan: TrainingPlan,
    plan_schema: TrainingPlanGenerationSchema,
    db: AsyncSession
) -> None:
    """
    Speichert den generierten Trainingsplan in der Datenbank.
    Diese Funktion ist von der Hauptfunktion getrennt, um klare Trennung zu gewährleisten.
    """
    # 1. Markdown für Rückwärtskompatibilität generieren
    markdown_summary = generate_markdown_summary(plan_schema)
    
    # 2. Plan-Schema in JSON-serialisierbares Dictionary umwandeln
    plan_dict = json.loads(
        json.dumps(plan_schema.model_dump(), cls=DateEncoder)
    )
    
    # 3. Datenbankoperationen ausführen
    training_plan.training_principles = markdown_summary
    training_plan.training_principles_json = plan_dict
    
    db.add(training_plan)
    await db.commit()
    await db.refresh(training_plan)

def generate_markdown_summary(plan: TrainingPlanGenerationSchema) -> str:
    """Generate a markdown summary from the structured plan for backward compatibility"""
    
    markdown = []
    
    # Personal information
    markdown.append("# Persönliche Informationen")
    markdown.append(plan.personal_information.content)
    markdown.append("")
    
    # Standard equipment
    markdown.append("# Standard Ausrüstung")
    markdown.append(plan.standard_equipment.content)
    markdown.append("")
    
    # Training principles
    markdown.append("# Trainingsprinzipien")
    markdown.append(plan.training_principles.content)
    markdown.append("")
    
    # Training phases
    markdown.append("# Trainingsphasen")
    markdown.append(plan.training_phases.content)
    markdown.append("")
    
    # Remarks
    markdown.append("# Bemerkungen")
    markdown.append(plan.remarks.content)
    markdown.append("")
    
    # Valid until
    markdown.append(f"*Gültig bis: {plan.valid_until.isoformat()}*")
    
    return "\n".join(markdown) 