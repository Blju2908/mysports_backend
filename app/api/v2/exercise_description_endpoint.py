from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.session import get_session
from app.services.exercise_description_service import (
    get_all_exercise_descriptions,
    get_exercise_description_by_name
)
from app.schemas.exercise_description_schema import ExerciseDescriptionRead
from app.core.auth import get_current_user, User

router = APIRouter(tags=["exercise-descriptions"])


@router.get("/", response_model=List[ExerciseDescriptionRead])
async def get_exercise_descriptions(
    response: Response,
    category: Optional[str] = Query(None, description="Filter by muscle group category"),
    search: Optional[str] = Query(None, description="Search term for exercise names"),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> List[ExerciseDescriptionRead]:
    """
    Get all exercise descriptions with optional filtering.
    
    Since exercise descriptions rarely change, this endpoint sets cache headers
    to enable client-side caching for 24 hours.
    """
    # Set cache headers for 24-hour caching
    response.headers["Cache-Control"] = "public, max-age=86400"
    
    exercises = await get_all_exercise_descriptions(
        db=db,
        category=category,
        search=search
    )
    
    return exercises


@router.get("/{name_german}", response_model=ExerciseDescriptionRead)
async def get_exercise_description(
    name_german: str,
    response: Response,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
) -> ExerciseDescriptionRead:
    """
    Get a specific exercise description by German name.
    """
    # Set cache headers for 24-hour caching
    response.headers["Cache-Control"] = "public, max-age=86400"
    
    exercise = await get_exercise_description_by_name(db=db, name=name_german)
    
    if not exercise:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Exercise description not found")
    
    return exercise