from sqlmodel import SQLModel, Field, Column
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import JSON, String, Boolean, Index, Float, Integer
from enum import Enum


class ExerciseDescription(SQLModel, table=True):
    """
    Übungsbeschreibungen - optimiert für SQLModel/Supabase Best Practices.
    
    Features:
    - Stabile Primary Key (name_german) für Uploads
    - Basic Indexing für Standard-Filterung
    - Vollständige Schema-Kompatibilität
    
    📝 GIN-Indexes für JSON-Arrays: Später hinzufügen wenn >1000 Übungen und häufige Equipment-Filter
    """
    __tablename__ = "exercise_descriptions"
    
    # === PRIMARY KEY & IDENTIFIERS ===
    name_german: str = Field(
        primary_key=True, 
        max_length=255,
        description="Deutscher Name als stabiler Primary Key"
    )
    name_english: str = Field(max_length=255, index=True)
    aliases: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Alternative names for the exercise"
    )
    
    # === CORE DESCRIPTION ===
    description_german: str = Field(max_length=1000)
    
    # === CLASSIFICATION ===
    difficulty_level: str = Field(
        max_length=50,
        index=True,  # ✅ Häufige Filterung erwartet
        description="beginner, intermediate, advanced, expert"
    )
    exercise_type: str = Field(
        max_length=50,
        index=True,
        description="strength, cardio, flexibility, plyometric, isometric"
    )
    primary_movement_pattern: str = Field(
        max_length=50,
        index=True,  # ✅ Wichtig für Trainingsplanung
        description="Push, Pull, Squat, Hip Hinge, Carry, Rotation, Isometric"
    )
    movement_pattern: str = Field(
        max_length=50,
        index=True,
        description="Specific movement pattern like push_horizontal, pull_vertical, etc."
    )
    is_unilateral: bool = Field(
        default=False,
        index=True,  # ✅ Binäre Filterung, simpel aber nützlich
        description="True wenn einseitig/asymmetrisch ausgeführt"
    )
    is_compound: bool = Field(
        default=True,
        index=True,
        description="True if compound movement, False if isolation"
    )
    
    # === MUSCLE ACTIVATION DATA ===
    muscle_activations: List[Dict[str, Any]] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Muscle group activations with percentages: [{'muscle_group': 'chest', 'activation_percentage': 90}]"
    )
    
    # === EQUIPMENT & REQUIREMENTS ===
    equipment_list: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Required equipment as JSON Array"
    )
    
    # === EXECUTION INSTRUCTIONS ===
    setup_steps: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Setup instructions as JSON Array"
    )
    execution_steps: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Execution steps as JSON Array"
    )
    common_mistakes: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Common mistakes to avoid as JSON Array"
    )
    
    # === VOLUME & PROGRAMMING ===
    volume_unit: str = Field(
        max_length=30,
        index=True,
        description="reps_only, reps_and_weight, time_based, distance_based"
    )
    typical_rep_range: str = Field(
        max_length=20,
        description="Typical rep range like '6-10' or '30-60s'"
    )
    
    # === RECOVERY & FATIGUE DATA ===
    met_value: float = Field(
        default=5.0,
        sa_column=Column(Float),
        description="Metabolic equivalent for energy expenditure calculation"
    )
    muscle_fatigue_factor: float = Field(
        default=1.0,
        sa_column=Column(Float),
        description="Exercise-specific fatigue multiplier (0.5-2.0)"
    )
    muscle_recovery_hours: int = Field(
        default=24,
        sa_column=Column(Integer),
        description="Recommended recovery hours for muscle groups"
    )
    recovery_complexity: str = Field(
        max_length=20,
        description="low, medium, high, very_high"
    )
    
    # === TIMESTAMPS ===
    created_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True  # ✅ Für "Newest first" Sortierung
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        index=True
    )
    
    # === BASIC INDEXES für häufige Kombinationen ===
    __table_args__ = (
        # ✅ Composite Index für Filter-Kombinationen
        Index(
            'ix_exercise_difficulty_pattern',
            'difficulty_level',
            'primary_movement_pattern'
        ),
        # ✅ Name-basierte Suche (Text-Pattern)
        Index(
            'ix_exercise_names_text',
            'name_german',
            'name_english'
        ),
    )

    def __repr__(self) -> str:
        return f"<ExerciseDescription(name='{self.name_german}', difficulty='{self.difficulty_level}')>" 