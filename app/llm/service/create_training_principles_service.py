from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.trainingplan_db_access import get_training_plan_for_user
from app.llm.chains.training_principles_chain import generate_training_principles
from app.llm.schemas.training_principles_schemas import TrainingPrinciplesSchema
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select, update
import json
from datetime import date

class DateEncoder(json.JSONEncoder):
    """JSON-Encoder, der date-Objekte automatisch in ISO-Format-Strings umwandelt."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

async def run_training_principles_chain(
    user_id: UUID | None,
    db: AsyncSession
) -> TrainingPrinciplesSchema:
    """
    Lädt die Trainingsziele des Nutzers und leitet daraus Trainingsprinzipien als 
    strukturiertes JSON ab.

    Args:
        user_id: Die ID des Benutzers
        db: Die Datenbankverbindung

    Returns:
        Die abgeleiteten Trainingsprinzipien als TrainingPrinciplesSchema
    """
    # 1. Trainingsplan laden (falls user_id vorhanden)
    training_plan = None
    if user_id is not None:
        training_plan = await get_training_plan_for_user(user_id, db)
        if training_plan is None:
            raise ValueError("Kein Trainingsplan für den Nutzer gefunden.")
    
    # 2. Daten für LLM-Anfrage vorbereiten
    training_goals = None
    if training_plan is not None:
        training_goals = training_plan.model_dump()

    # 3. LLM-Call durchführen
    principles_schema = await generate_training_principles(training_goals)
    
    # 4. Wenn user_id vorhanden, Ergebnisse in Datenbank speichern
    if user_id is not None and training_plan is not None:
        await save_principles_to_db(training_plan, principles_schema, db)
    
    return principles_schema

async def save_principles_to_db(
    training_plan: TrainingPlan,
    principles_schema: TrainingPrinciplesSchema,
    db: AsyncSession
) -> None:
    """
    Speichert die generierten Trainingsprinzipien in der Datenbank.
    Diese Funktion ist von der Hauptfunktion getrennt, um klare Trennung zu gewährleisten.
    """
    # 1. Markdown für Rückwärtskompatibilität generieren
    markdown_summary = generate_markdown_summary(principles_schema)
    
    # 2. Prinzipien-Schema in JSON-serialisierbares Dictionary umwandeln
    principles_dict = json.loads(
        json.dumps(principles_schema.model_dump(), cls=DateEncoder)
    )
    
    # 3. Datenbankoperationen ausführen
    training_plan.training_principles = markdown_summary
    training_plan.training_principles_json = principles_dict
    
    db.add(training_plan)
    await db.commit()
    await db.refresh(training_plan)

def generate_markdown_summary(principles: TrainingPrinciplesSchema) -> str:
    """Generate a markdown summary from the structured principles for backward compatibility"""
    
    markdown = []
    
    # Person overview
    overview = principles.person_overview
    markdown.append("# Übersicht Person")
    markdown.append(f"**Basisdaten:** {overview.base_data}")
    markdown.append(f"**Trainingsziele:** {overview.training_goals}")
    markdown.append(f"**Trainingserfahrung:** {overview.experience_level}")
    markdown.append(f"**Trainingsumgebung:** {overview.training_environment}")
    if overview.limitations:
        markdown.append(f"**Einschränkungen:** {overview.limitations}")
    markdown.append("")
    
    # Core principles
    markdown.append("# Kernprinzipien")
    for principle in principles.core_principles:
        markdown.append(f"**{principle.name}:** {principle.explanation}")
    markdown.append("")
    
    # Training recommendation
    markdown.append("# Trainingsempfehlung")
    markdown.append(principles.training_recommendation)
    markdown.append("")
    
    # Training phases
    markdown.append("# Trainingsphasen")
    for phase in principles.training_phases:
        markdown.append(f"## {phase.name} ({phase.duration})")
        markdown.append(f"**Fokus:** {phase.focus}")
        markdown.append(f"**Beschreibung:** {phase.description}")
        markdown.append("**Workout-Typen:**")
        for workout in phase.workout_types:
            markdown.append(f"- {workout.type}: {workout.intensity}")
        markdown.append("")
    
    # Valid until
    markdown.append(f"*Gültig bis: {principles.valid_until.isoformat()}*")
    
    return "\n".join(markdown) 