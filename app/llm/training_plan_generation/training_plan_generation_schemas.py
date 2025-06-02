from pydantic import BaseModel, Field
from typing import Optional
from datetime import date

class PersonalInformationSchema(BaseModel):
    """Personal information about the user"""
    content: str = Field(..., description="Freitext mit Alter, Zielen, Häufigkeit & Einheitendauer, Erfahrungslevel, allgemeinem Fitnesslevel, Einschränkungen")

class StandardEquipmentSchema(BaseModel):
    """Standard equipment and training environment"""
    content: str = Field(..., description="Freitext zur Beschreibung der normalen Trainingsumgebung und verfügbaren Ausrüstung")

class TrainingPrinciplesSchema(BaseModel):
    """Training principles section"""
    content: str = Field(..., description="Freitext zur Beschreibung von 3-5 wichtigen Trainingsprinzipien mit Erklärungen")

class TrainingPhasesSchema(BaseModel):
    """Training phases section"""
    content: str = Field(..., description="Freitext zur Beschreibung der Trainingsphasen mit Dauer, Fokus, Beschreibung und Workout-Typen")

class RemarksSchema(BaseModel):
    """Individual remarks and preferences"""
    content: str = Field(..., description="Freitext für individuelle Nutzerwünsche und persönliche Erinnerungen/Notizen")

class TrainingPlanGenerationSchema(BaseModel):
    """Complete simplified training plan structure with 5 editable text blocks"""
    personal_information: PersonalInformationSchema = Field(..., description="Bereich für persönliche Informationen")
    standard_equipment: StandardEquipmentSchema = Field(..., description="Bereich für Ausrüstung und Umgebung")
    training_principles: TrainingPrinciplesSchema = Field(..., description="Bereich für Trainingsprinzipien")
    training_phases: TrainingPhasesSchema = Field(..., description="Bereich für Trainingsphasen")
    remarks: RemarksSchema = Field(..., description="Bereich für individuelle Anmerkungen und Präferenzen")
    valid_until: date = Field(..., description="Datum bis zu dem dieser Trainingsplan gültig ist")