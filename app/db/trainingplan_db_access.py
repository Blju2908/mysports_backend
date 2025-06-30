from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.training_plan_model import TrainingPlan


def filter_training_history(training_history: list) -> list[dict]:
    """
    Gibt eine gekürzte Liste der Trainingshistorie zurück, nur mit relevanten Feldern und ohne None-Werte.
    Relevante Felder: exercise_name, timestamp, reps, weight, duration, rest_time
    """
    relevant_fields = [
        "exercise_name", "timestamp", "reps", "weight", "duration", "rest_time"
    ]
    filtered = []
    for entry in training_history:
        entry_dict = entry.model_dump() if hasattr(entry, "model_dump") else dict(entry)
        reduced = {k: v for k, v in entry_dict.items() if k in relevant_fields and v is not None}
        filtered.append(reduced)
    return filtered