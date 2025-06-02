from pydantic import BaseModel, Field
from typing import Optional
from datetime import date
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema


class TrainingPlanRevisionRequestSchema(BaseModel):
    """Schema for training plan revision requests."""
    user_request: str = Field(..., description="Benutzeranfrage zur gewünschten Änderung des Trainingsplans")
    current_training_plan: TrainingPlanGenerationSchema = Field(..., description="Der aktuelle Trainingsplan als Kontext")
    user_context: Optional[str] = Field(default=None, description="Zusätzlicher Benutzerkontext oder Präferenzen")


class TrainingPlanRevisionResponseSchema(BaseModel):
    """Schema for training plan revision responses."""
    user_request: str = Field(..., description="Die ursprüngliche Benutzeranfrage")
    revised_training_plan: TrainingPlanGenerationSchema = Field(..., description="Der überarbeitete Trainingsplan")
    changes_summary: str = Field(..., description="Zusammenfassung der durchgeführten Änderungen")
    revision_timestamp: str = Field(..., description="Zeitstempel der Überarbeitung")


class TrainingPlanRevisionPreviewSchema(BaseModel):
    """Schema for training plan revision preview (before confirmation)."""
    revised_training_plan: TrainingPlanGenerationSchema = Field(..., description="Der überarbeitete Trainingsplan (Vorschau)")
    changes_summary: str = Field(..., description="Zusammenfassung der geplanten Änderungen")
    original_request: str = Field(..., description="Die ursprüngliche Benutzeranfrage")


class TrainingPlanRevisionConfirmationSchema(BaseModel):
    """Schema for confirming a training plan revision."""
    confirm: bool = Field(..., description="Bestätigung der Überarbeitung")
    apply_changes: bool = Field(default=True, description="Änderungen auf den aktuellen Plan anwenden")
    save_as_backup: bool = Field(default=True, description="Eine Sicherungskopie des alten Plans erstellen") 