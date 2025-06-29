from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class MuscleGroup(str, Enum):
    """Standardisierte Muskelgruppen für Personal Trainer - MECE optimiert"""
    
    # === PRIMÄRE MUSKELGRUPPEN (Hauptkategorien) ===
    
    # Oberkörper
    BRUST = "Brust"
    RUECKEN = "Rücken" 
    SCHULTERN = "Schultern"
    BIZEPS = "Bizeps"
    TRIZEPS = "Trizeps"
    UNTERARME = "Unterarme"
    
    # Unterkörper
    QUADRIZEPS = "Oberschenkel-Vorderseite"
    HAMSTRINGS = "Oberschenkel-Rückseite"
    GESAESS = "Gesäß"
    WADEN = "Waden"
    SCHIENBEIN = "Schienbein"
    
    # Rumpf
    BAUCHMUSKELN = "Bauchmuskeln"
    CORE = "Rumpfstabilität"
    UNTERER_RUECKEN = "Unterer Rücken"
    
    # === SPEZIFISCHE BEREICHE (bei Bedarf für detailliertere Beschreibungen) ===
    
    # Brust-Spezifizierung
    OBERE_BRUST = "Obere Brust"
    UNTERE_BRUST = "Untere Brust"
    
    # Rücken-Spezifizierung  
    LATISSIMUS = "Breiter Rückenmuskel"
    TRAPEZMUSKEL = "Trapezmuskel"
    RHOMBOIDEN = "Rhomboiden"
    
    # Schulter-Spezifizierung
    VORDERE_SCHULTER = "Vordere Schulter"
    SEITLICHE_SCHULTER = "Seitliche Schulter"  
    HINTERE_SCHULTER = "Hintere Schulter"
    ROTATORENMANSCHETTE = "Rotatorenmanschette"
    
    # Bauch-Spezifizierung
    GERADE_BAUCHMUSKELN = "Gerade Bauchmuskeln"
    SEITLICHE_BAUCHMUSKELN = "Seitliche Bauchmuskeln"
    TIEFE_BAUCHMUSKELN = "Tiefe Bauchmuskeln"
    
    # Bein-Spezifizierung
    ADDUKTOREN = "Beininnenseite"
    ABDUKTOREN = "Beinaußenseite"
    GESAESS_GROSS = "Großer Gesäßmuskel"
    GESAESS_MITTEL = "Mittlerer Gesäßmuskel"
    
    # === FUNKTIONELLE KATEGORIEN ===
    
    # Ganzkörper
    GANZKOERPER = "Ganzkörper"
    MEHRERE_MUSKELGRUPPEN = "Mehrere Muskelgruppen"
    
    # Fitness-Komponenten
    AUSDAUER = "Ausdauer"
    KRAFT = "Kraft"
    KOORDINATION = "Koordination"
    GLEICHGEWICHT = "Gleichgewicht"
    BEWEGLICHKEIT = "Beweglichkeit"
    STABILISATION = "Stabilisation"
    
    # === BEWEGLICHKEIT & MOBILITY ===
    
    # Körperregionen
    NACKEN = "Nacken"
    WIRBELSAEULE = "Wirbelsäule"
    HUEFTE = "Hüfte"
    SCHULTERGELENK = "Schultergelenk"
    
    # Spezifische Mobility-Bereiche
    HUEFTE_FLEXOREN = "Hüftbeuger"
    HUEFTE_EXTENSOREN = "Hüftstrecker"
    HINTERE_KETTE = "Hintere Muskelkette"
    VORDERE_KETTE = "Vordere Muskelkette"
    
    # Regeneration
    ENTSPANNUNG = "Entspannung"
    REGENERATION = "Regeneration"

class ExerciseDescriptionSchema(BaseModel):
    """Schema für eine detaillierte Übungsbeschreibung"""
    name_german: str = Field(..., description="Name der Übung auf Deutsch")
    name_english: str = Field(..., description="Name der Übung auf Englisch")
    description_german: str = Field(..., description="Kurze sachliche Beschreibung der Übung in einem kurzen präzisen Halbsatz.")
    equipment_options: List[str] = Field(..., description="Liste möglicher Equipment-Optionen")
    target_muscle_groups: List[MuscleGroup] = Field(..., description="Liste der Hauptmuskelgruppen")
    execution_steps: List[str] = Field(..., description="Nummerierte Ausführungsschritte") 