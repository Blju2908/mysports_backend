"""
Optimiertes, MECE-konformes Datenmodell für Übungsbibliothek
mit konsistenter Normalisierung und verbesserter Wiederverwendbarkeit.
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum

# === NORMALISIERTE ENUMS (MECE-konform) ===


class DifficultyLevel(str, Enum):
    """Normalisierte Schwierigkeitsgrade"""

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class ExerciseType(str, Enum):
    """Hauptkategorien von Übungen (MECE)"""

    STRENGTH = "strength"  # Krafttraining mit Gewichten
    CARDIO = "cardio"  # Ausdauertraining
    FLEXIBILITY = "flexibility"  # Dehnungsübungen
    MOBILITY = "mobility"  # Beweglichkeitsübungen
    STABILITY = "stability"  # Stabilisationsübungen
    PLYOMETRIC = "plyometric"  # Explosivkrafttraining
    REHABILITATION = "rehabilitation"  # Reha-Übungen


class MovementPattern(str, Enum):
    """Primäre Bewegungsmuster (MECE, biomechanisch fundiert)"""

    PUSH_VERTICAL = "push_vertical"  # Overhead press, pike push-up
    PUSH_HORIZONTAL = "push_horizontal"  # Push-up, bench press
    PULL_VERTICAL = "pull_vertical"  # Pull-up, lat pulldown
    PULL_HORIZONTAL = "pull_horizontal"  # Row, inverted row
    SQUAT = "squat"  # Squat variations
    HIP_HINGE = "hip_hinge"  # Deadlift, hip thrust
    LUNGE = "lunge"  # Single leg patterns
    CARRY = "carry"  # Loaded carries
    ROTATION = "rotation"  # Rotational movements
    ANTI_ROTATION = "anti_rotation"  # Core stability
    ISOMETRIC = "isometric"  # Static holds
    LOCOMOTION = "locomotion"  # Crawling, walking patterns


class MovementPlane(str, Enum):
    """Bewegungsebenen"""

    SAGITTAL = "sagittal"  # Vorwärts/Rückwärts
    FRONTAL = "frontal"  # Seitlich
    TRANSVERSE = "transverse"  # Rotational
    MULTIPLANAR = "multiplanar"  # Mehrere Ebenen


class MuscleGroup(str, Enum):
    """Normalisierte Muskelgruppen für konsistente Zuordnung"""

    # Oberkörper
    CHEST = "chest"
    SHOULDERS_ANTERIOR = "shoulders_anterior"
    SHOULDERS_LATERAL = "shoulders_lateral"
    SHOULDERS_POSTERIOR = "shoulders_posterior"
    TRICEPS = "triceps"
    BICEPS = "biceps"
    FOREARMS = "forearms"

    # Rücken
    LATISSIMUS = "latissimus"
    RHOMBOIDS = "rhomboids"
    MID_TRAPS = "mid_traps"
    LOWER_TRAPS = "lower_traps"
    UPPER_TRAPS = "upper_traps"
    REAR_DELTS = "rear_delts"

    # Core
    RECTUS_ABDOMINIS = "rectus_abdominis"
    OBLIQUES = "obliques"
    TRANSVERSE_ABDOMINIS = "transverse_abdominis"
    ERECTOR_SPINAE = "erector_spinae"

    # Unterkörper
    QUADRICEPS = "quadriceps"
    HAMSTRINGS = "hamstrings"
    GLUTES = "glutes"
    CALVES = "calves"
    HIP_FLEXORS = "hip_flexors"
    ADDUCTORS = "adductors"
    ABDUCTORS = "abductors"


class EquipmentCategory(str, Enum):
    """Ausrüstungskategorien (MECE)"""

    BODYWEIGHT = "bodyweight"
    FREE_WEIGHTS = "free_weights"
    MACHINES = "machines"
    RESISTANCE_BANDS = "resistance_bands"
    SUSPENSION = "suspension"
    CARDIO_EQUIPMENT = "cardio_equipment"
    STABILITY_TOOLS = "stability_tools"
    FUNCTIONAL_TOOLS = "functional_tools"


class Equipment(str, Enum):
    """Spezifische Ausrüstung"""

    # Bodyweight
    NONE = "none"

    # Free Weights
    BARBELL = "barbell"
    DUMBBELLS = "dumbbells"
    KETTLEBELL = "kettlebell"
    WEIGHT_PLATES = "weight_plates"

    # Machines
    CABLE_MACHINE = "cable_machine"
    LEG_PRESS = "leg_press"
    LAT_PULLDOWN = "lat_pulldown"

    # Resistance
    RESISTANCE_BANDS = "resistance_bands"
    MINI_BANDS = "mini_bands"

    # Suspension
    TRX = "trx"
    GYMNASTIC_RINGS = "gymnastic_rings"

    # Stability
    STABILITY_BALL = "stability_ball"
    BOSU_BALL = "bosu_ball"
    BALANCE_PAD = "balance_pad"

    # Functional
    MEDICINE_BALL = "medicine_ball"
    BATTLE_ROPES = "battle_ropes"
    PARALLETTES = "parallettes"
    PULL_UP_BAR = "pull_up_bar"

    # Cardio
    TREADMILL = "treadmill"
    ROWING_MACHINE = "rowing_machine"
    STATIONARY_BIKE = "stationary_bike"


class SpaceRequirement(str, Enum):
    """Platzbedarf"""

    MINIMAL = "minimal"  # 1x1m
    SMALL = "small"  # 2x2m
    MEDIUM = "medium"  # 3x3m
    LARGE = "large"  # 4x4m+
    OVERHEAD_SPACE = "overhead_space"  # Zusätzlich Platz nach oben


class VolumeUnit(str, Enum):
    """Einheiten für Volumenberechnung"""

    WEIGHT_REPS = "weight_reps"  # kg × Wiederholungen
    TIME_SECONDS = "time_seconds"  # Sekunden
    DISTANCE_METERS = "distance_meters"  # Meter
    REPS_ONLY = "reps_only"  # Nur Wiederholungen
    BODYWEIGHT_REPS = "bodyweight_reps"  # Körpergewicht × Wiederholungen


class RecoveryComplexity(str, Enum):
    """Komplexität der Muskelregeneration"""

    LOW = "low"  # 6-12h (Isolation, leichte Übungen)
    MODERATE = "moderate"  # 12-24h (moderate Compound-Übungen)
    HIGH = "high"  # 24-48h (schwere Compound-Übungen)
    VERY_HIGH = "very_high"  # 48-72h (sehr intensive/explosive Übungen)


# === VEREINFACHTE DATENMODELLE ===


class MuscleActivation(BaseModel):
    """Muskelaktivierung mit Intensität"""

    muscle_group: MuscleGroup
    activation_percentage: int = Field(
        ge=10, le=100, description="Aktivierung in % (10-100)"
    )


class ExerciseSchema(BaseModel):
    """Vereinfachtes, LLM-freundliches Übungsschema"""

    # === IDENTIFIKATION ===
    name_german: str = Field(min_length=1, max_length=100)
    name_english: str = Field(min_length=1, max_length=100)
    aliases: List[str] = Field(default_factory=list, description="Alternative Namen")

    # === BESCHREIBUNG ===
    description_german: str = Field(min_length=10, max_length=500)

    # === KLASSIFIZIERUNG ===
    exercise_type: ExerciseType
    difficulty_level: DifficultyLevel
    movement_pattern: MovementPattern

    # === MUSKELAKTIVIERUNG (vereinfacht) ===
    muscle_activations: List[MuscleActivation] = Field(
        min_items=1, description="Detaillierte Muskelaktivierung mit Prozentsätzen"
    )

    # === BIOMECHANIK ===
    is_unilateral: bool = Field(description="Einseitige Ausführung - Wird zuerst die eine und dann die andere Seite trainiert? Wenn man alternierend trainiert, dann ist das False!")
    is_compound: bool = Field(description="Mehrgelenkige Übung")

    # === AUSRÜSTUNG (vereinfacht) ===
    equipment_list: List[str] = Field(
        default_factory=list, description="Liste der benötigten Ausrüstung als Strings"
    )

    # === AUSFÜHRUNG ===
    setup_steps: List[str] = Field(description="Vorbereitung der Übung")
    execution_steps: List[str] = Field(min_items=2, description="Ausführungsschritte")
    common_mistakes: List[str] = Field(
        default_factory=list, description="Häufige Fehler"
    )

    # === VOLUMEN & INTENSITÄT (vereinfacht) ===
    volume_unit: VolumeUnit = Field(description="Einheit für Volumenberechnung")
    typical_rep_range: Optional[str] = Field(
        default=None, description="z.B. '8-12', '30-60s'"
    )

    met_value: float = Field(
        ge=1.0, le=10.0, description="Metabolischer Wert (MET) zwischen 1 und 10"
    )
    muscle_fatigue_factor: float = Field(
        ge=0.2,
        le=2.0,
        description="Faktor für die Muskelermüdung, je höher, desto mehr Muskelermüdung. Faktor für Volumenbasierte Berechnung der Muskelermüdung",
    )

    # === REGENERATION ===
    muscle_recovery_hours: int = Field(
        ge=0,
        le=72,
        description="Durchschnittliche Regenerationszeit der beteiligten Muskulatur in Stunden (6-72h)",
    )
    recovery_complexity: RecoveryComplexity = Field(
        description="Komplexitätsstufe der Regeneration basierend auf Übungsart und Intensität"
    )


# Wrapper class for structured output
class ExerciseListResponse(BaseModel):
    """Wrapper for list of exercises to work with Langchain structured output"""

    exercises: List[ExerciseSchema] = Field(description="Liste der erweiterten Übungen")
