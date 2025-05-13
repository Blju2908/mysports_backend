from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.trainingplan_db_access import get_training_plan_for_user
from app.llm.chains.training_principles_chain import generate_training_principles
from typing import Any

async def run_training_principles_chain(
    user_id: UUID | None,
    db: AsyncSession
) -> Any:
    """
    Lädt die Trainingsziele des Nutzers und leitet daraus Trainingsprinzipien ab.

    Args:
        user_id: Die ID des Benutzers
        db: Die Datenbankverbindung

    Returns:
        Die abgeleiteten Trainingsprinzipien (LLM-Output)
    """
    if user_id is not None:
        training_plan = await get_training_plan_for_user(user_id, db)
        if training_plan is None:
            raise ValueError("Kein Trainingsplan für den Nutzer gefunden.")
        # Extrahiere relevante Ziele aus dem Trainingsplan
        training_goals = training_plan.model_dump()
    else:
        training_goals = None

    # LLM-Call durchführen
    result = await generate_training_principles(training_goals)
    return result 