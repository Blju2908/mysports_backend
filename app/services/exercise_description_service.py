from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.exercise_description_model import ExerciseDescription


async def get_all_exercise_descriptions(
    db: AsyncSession,
    category: Optional[str] = None,
    search: Optional[str] = None
) -> List[ExerciseDescription]:
    """
    Retrieves all exercise descriptions with optional filtering.
    
    Args:
        db: The asynchronous database session.
        category: Optional category filter (e.g., "Brust", "Rücken").
        search: Optional search term for exercise names.
    
    Returns:
        List of ExerciseDescription objects.
    """
    query = select(ExerciseDescription)
    
    # Apply category filter if provided
    if category:
        # Filter by muscle groups containing the category
        query = query.where(
            ExerciseDescription.target_muscle_groups.contains([category])
        )
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.where(
            (ExerciseDescription.name_german.ilike(search_term)) |
            (ExerciseDescription.name_english.ilike(search_term))
        )
    
    # Order by name for consistent results
    query = query.order_by(ExerciseDescription.name_german)
    
    result = await db.execute(query)
    return result.scalars().all()


async def get_exercise_description_by_name(
    db: AsyncSession,
    name: str
) -> Optional[ExerciseDescription]:
    """
    Retrieves a single exercise description by German name.
    
    Args:
        db: The asynchronous database session.
        name: The German name of the exercise (primary key).
    
    Returns:
        ExerciseDescription object or None if not found.
    """
    result = await db.execute(
        select(ExerciseDescription).where(ExerciseDescription.name_german == name)
    )
    return result.scalar_one_or_none()