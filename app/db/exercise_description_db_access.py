from typing import List, Optional
from sqlmodel import select, or_, and_
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import func, text, cast
from sqlalchemy.dialects.postgresql import JSONB
from app.models.exercise_description_model import ExerciseDescription


# ✅ PRAGMATISCHE SQLMODEL QUERIES (ohne GIN-Index Dependency)

async def get_exercise_by_name(
    db: AsyncSession, 
    name_german: str
) -> Optional[ExerciseDescription]:
    """
    ✅ SQLModel One-Liner für Primary Key Lookup
    """
    return await db.get(ExerciseDescription, name_german)


async def search_exercises_by_equipment(
    db: AsyncSession,
    equipment_list: List[str],
    limit: int = 20
) -> List[ExerciseDescription]:
    """
    ✅ Pragmatische JSON Array Filterung (funktioniert auch ohne GIN-Index)
    """
    # Einfacher JSON Contains Operator - PostgreSQL optimiert das automatisch
    conditions = []
    for equipment in equipment_list:
        conditions.append(
            cast(ExerciseDescription.equipment_options, JSONB).op('@>')(cast([equipment], JSONB))
        )
    
    result = await db.scalars(
        select(ExerciseDescription)
        .where(or_(*conditions))
        .order_by(ExerciseDescription.name_german)
        .limit(limit)
    )
    return result.all()


async def filter_exercises_advanced(
    db: AsyncSession,
    muscle_groups: Optional[List[str]] = None,
    equipment: Optional[List[str]] = None,
    difficulty_levels: Optional[List[str]] = None,
    movement_patterns: Optional[List[str]] = None,
    is_unilateral: Optional[bool] = None,
) -> List[ExerciseDescription]:
    """
    ✅ Kombinierte Filterung - pragmatisch und performant
    Returns fully-loaded objects to prevent session detachment issues.
    """
    query = select(ExerciseDescription)
    
    # ✅ Standard Field Filtering (nutzt normale B-Tree Indexes)
    if difficulty_levels:
        query = query.where(ExerciseDescription.difficulty_level.in_(difficulty_levels))
    
    if movement_patterns:
        query = query.where(ExerciseDescription.primary_movement_pattern.in_(movement_patterns))
    
    if is_unilateral is not None:
        query = query.where(ExerciseDescription.is_unilateral == is_unilateral)
    
    # ✅ Einfache JSON Array Filterung (auch ohne GIN performant bei <1000 rows)
    if muscle_groups:
        muscle_conditions = []
        for muscle in muscle_groups:
            muscle_conditions.append(
                cast(ExerciseDescription.target_muscle_groups, JSONB).op('@>')(cast([muscle], JSONB))
            )
        query = query.where(or_(*muscle_conditions))
    
    if equipment:
        equipment_conditions = []
        for eq in equipment:
            equipment_conditions.append(
                cast(ExerciseDescription.equipment_options, JSONB).op('@>')(cast([eq], JSONB))
            )
        query = query.where(or_(*equipment_conditions))
    
    # ✅ Ordering und Limiting
    query = query.order_by(ExerciseDescription.name_german)
    
    result = await db.scalars(query)
    return result.all()


async def get_all_exercise_names(db: AsyncSession) -> List[ExerciseDescription]:
    """
    Lädt alle Übungen aus der Datenbank mit Namen, Schwierigkeit und Equipment.
    Optimiert für Exercise Library Generation.
    """
    query = select(ExerciseDescription).order_by(ExerciseDescription.name_german)
    result = await db.scalars(query)
    return result.all()


async def get_equipment_list(db: AsyncSession) -> List[str]:
    """Gibt eine alphabetisch sortierte Liste aller einzigartigen Equipment-Strings zurück."""
    # ✅ SQLModel Best Practice: select + func + distinct
    stmt = (
        select(func.distinct(func.json_array_elements_text(ExerciseDescription.equipment_options)))
        .order_by(func.json_array_elements_text(ExerciseDescription.equipment_options))
    )
    result = await db.execute(stmt)
    # row[0] enthält den Equipment-String
    return [row[0] for row in result.fetchall()]


async def get_muscle_groups_list(db: AsyncSession) -> List[str]:
    """Gibt eine alphabetisch sortierte Liste aller einzigartigen Muskelgruppen zurück."""
    stmt = (
        select(func.distinct(func.json_array_elements_text(ExerciseDescription.target_muscle_groups)))
        .order_by(func.json_array_elements_text(ExerciseDescription.target_muscle_groups))
    )
    result = await db.execute(stmt)
    return [row[0] for row in result.fetchall()]


async def search_exercises_by_text(
    db: AsyncSession,
    search_term: str,
    limit: int = 20
) -> List[ExerciseDescription]:
    """
    ✅ Text-basierte Suche (nutzt name_indexes)
    """
    search_pattern = f"%{search_term.lower()}%"
    
    result = await db.scalars(
        select(ExerciseDescription)
        .where(
            or_(
                func.lower(ExerciseDescription.name_german).contains(search_pattern),
                func.lower(ExerciseDescription.name_english).contains(search_pattern),
                func.lower(ExerciseDescription.description_german).contains(search_pattern)
            )
        )
        .order_by(ExerciseDescription.name_german)
        .limit(limit)
    )
    return result.all()


async def get_exercises_by_difficulty_stats(db: AsyncSession) -> dict:
    """
    ✅ Einfache Aggregation für Dashboard/Statistics
    """
    result = await db.execute(
        select(
            ExerciseDescription.difficulty_level,
            func.count(ExerciseDescription.name_german).label('count')
        )
        .group_by(ExerciseDescription.difficulty_level)
        .order_by(ExerciseDescription.difficulty_level)
    )
    
    return {row[0]: row[1] for row in result.fetchall()}


# ✅ BULK OPERATIONS

async def bulk_insert_exercises(
    db: AsyncSession,
    exercises: List[ExerciseDescription]
) -> None:
    """
    ✅ Bulk Insert - SQLModel Best Practice
    """
    db.add_all(exercises)
    await db.commit()


# 📝 Performance-Upgrade für später (wenn >1000 Übungen):
"""
async def search_exercises_by_equipment_with_gin(
    db: AsyncSession,
    equipment_list: List[str],
    limit: int = 20
) -> List[ExerciseDescription]:
    # Nutzt GIN-Index für super-schnelle Array-Suche
    conditions = []
    for equipment in equipment_list:
        conditions.append(
            func.jsonb_path_exists(
                ExerciseDescription.equipment_options,
                f'$[*] ? (@ == "{equipment}")'
            )
        )
    
    result = await db.scalars(
        select(ExerciseDescription)
        .where(or_(*conditions))
        .limit(limit)
    )
    return result.all()
""" 