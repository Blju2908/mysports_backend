from sqlmodel import SQLModel, Field, Column
from typing import List, Optional
from datetime import datetime
from sqlalchemy import JSON, String, Boolean, Index
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
    
    # === CORE DESCRIPTION ===
    description_german: str = Field(max_length=1000)
    
    # === CLASSIFICATION ===
    difficulty_level: str = Field(
        max_length=50,
        index=True,  # ✅ Häufige Filterung erwartet
        description="Anfänger, Fortgeschritten, oder Experte"
    )
    primary_movement_pattern: str = Field(
        max_length=50,
        index=True,  # ✅ Wichtig für Trainingsplanung
        description="Push, Pull, Squat, Hip Hinge, Carry, Rotation, Isometric"
    )
    is_unilateral: bool = Field(
        default=False,
        index=True,  # ✅ Binäre Filterung, simpel aber nützlich
        description="True wenn einseitig/asymmetrisch ausgeführt"
    )
    
    # === JSON ARRAYS (erstmal ohne GIN-Indexes) ===
    equipment_options: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Equipment-Optionen als JSON Array"
    )
    target_muscle_groups: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Zielmuskelgruppen als JSON Array"
    )
    execution_steps: List[str] = Field(
        default_factory=list,
        sa_column=Column(JSON),
        description="Ausführungsschritte als JSON Array"
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
    
    # TODO: GIN-Indexes später hinzufügen wenn nötig:
    # Index('ix_exercise_equipment_gin', 'equipment_options', postgresql_using='gin'),
    # Index('ix_exercise_muscles_gin', 'target_muscle_groups', postgresql_using='gin'),

    def __repr__(self) -> str:
        return f"<ExerciseDescription(name='{self.name_german}', difficulty='{self.difficulty_level}')>" 