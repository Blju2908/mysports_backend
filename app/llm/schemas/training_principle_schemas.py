from pydantic import BaseModel, Field
from typing import List

class TrainingPrincipleSchema(BaseModel):
    name: str = Field(..., description="Name des Trainingsprinzips")
    description: str = Field(..., description="Kurze Erklärung des Prinzips")

class TrainingPrinciplesResponseSchema(BaseModel):
    principles: List[TrainingPrincipleSchema] = Field(..., description="Liste der abgeleiteten Trainingsprinzipien")
    summary: str = Field(..., description="Zusammenfassende Erklärung der Trainingsphilosophie für den Nutzer") 