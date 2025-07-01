from pydantic import BaseModel, Field
from typing import List
from enum import Enum

class MuscleGroup(str, Enum):
    """Optimierte Muskelgruppen für Personal Trainer - Balance zwischen Spezifität und Praktikabilität"""
    
    # === OBERKÖRPER ===
    BRUST = "Brust"
    RUECKEN = "Rücken"
    SCHULTERN = "Schultern"
    BIZEPS = "Bizeps"
    TRIZEPS = "Trizeps"
    
    # Rücken-Spezifizierung (wichtig für Trainingsplanung)
    LATISSIMUS = "Latissimus"
    TRAPEZMUSKEL = "Trapezmuskel"
    
    # Schulter-Spezifizierung (wichtig für Verletzungsprävention)
    VORDERE_SCHULTER = "Vordere Schulter"
    SEITLICHE_SCHULTER = "Seitliche Schulter"
    HINTERE_SCHULTER = "Hintere Schulter"
    
    # === UNTERKÖRPER ===
    QUADRIZEPS = "Oberschenkel-Vorderseite"
    HAMSTRINGS = "Oberschenkel-Rückseite"
    GESAESS = "Gesäß"
    WADEN = "Waden"
    
    # Wichtige Spezifizierungen für Funktionalität
    ADDUKTOREN = "Beininnenseite"
    ABDUKTOREN = "Beinaußenseite"
    
    # === RUMPF ===
    BAUCHMUSKELN = "Bauchmuskeln"
    CORE = "Rumpfstabilität"
    UNTERER_RUECKEN = "Unterer Rücken"
    
    # === FUNKTIONELLE KATEGORIEN ===
    GANZKOERPER = "Ganzkörper"
    BEWEGLICHKEIT = "Beweglichkeit"
    AUSDAUER = "Ausdauer"

class DifficultyLevel(str, Enum):
    """Schwierigkeitsgrade für Übungen"""
    ANFAENGER = "Anfänger"
    FORTGESCHRITTEN = "Fortgeschritten"
    EXPERTE = "Experte"

class MovementPattern(str, Enum):
    """Grundlegende Bewegungsmuster im Krafttraining"""
    PUSH = "Push"
    PULL = "Pull"
    SQUAT = "Squat"
    HIP_HINGE = "Hip Hinge"
    CARRY = "Carry"
    ROTATION = "Rotation"
    ISOMETRIC = "Isometric"

class Equipment(str, Enum):
    """Trainingsgeräte und Equipment für Übungen - Matte wird als Standard angenommen"""
    
    # === KEIN ZUSÄTZLICHES EQUIPMENT ===
    BODYWEIGHT = "Eigengewicht"
    
    # === HOME EQUIPMENT ===
    RESISTANCE_BAND = "Widerstandsband"
    DUMBBELLS = "Kurzhanteln"
    BARBELL = "Langhantel"
    MEDICINE_BALL = "Medizinball"
    
    # === ERHÖHUNGEN UND STÜTZEN ===
    BENCH = "Bank"
    BOX = "Box/Kasten"
    STEP = "Stufe/Step"
    WALL = "Wand"
    
    # === BASIC GYM EQUIPMENT ===
    PULL_UP_BAR = "Klimmzugstange"
    PARALLEL_BARS = "Parallelbarren"
    RINGS = "Turnringe"
    
    # === GYM MASCHINEN (Hauptkategorien) ===
    GYM_MACHINE = "Gym Maschine"
    
    # === SPEZIAL EQUIPMENT ===
    TRX_BAND = "TRX Band"  # TRX etc.
    BATTLE_ROPES = "Battle Ropes"
    KETTLEBELL = "Kettlebell"

    # === CARDIO EQUIPMENT ===
    TREADMILL = "Laufband"
    BIKE = "Fahrrad"
    ROWING_MACHINE = "Rudergerät"
    ASSAULT_BIKE = "Assault Bike"
    STEPMILL = "Stepmill"
    SKIERG = "Skierg"


class ExerciseDescriptionSchema(BaseModel):
    """Schema für die Generierung von Übungsbeschreibungen"""
    
    name_german: str = Field(description="Deutscher Name der Übung")
    name_english: str = Field(description="Englischer Name der Übung")
    description_german: str = Field(description="Kurze, präzise Beschreibung auf Deutsch")
    
    difficulty_level: DifficultyLevel = Field(description="Schwierigkeitsgrad der Übung")
    primary_movement_pattern: MovementPattern = Field(description="Hauptbewegungsmuster")
    is_unilateral: bool = Field(description="True wenn die Übung einseitig/asymmetrisch ausgeführt wird")
    
    equipment_options: List[str] = Field(description="Benötigte Ausrüstung")
    target_muscle_groups: List[str] = Field(description="Zielmuskelgruppen")
    execution_steps: List[str] = Field(description="Schritt-für-Schritt Ausführung")


class ExerciseDescriptionListSchema(BaseModel):
    """Schema für Listen von Übungsbeschreibungen"""
    exercises: List[ExerciseDescriptionSchema]