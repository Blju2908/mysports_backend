from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.llm.service.run_workout_chain import run_workout_chain
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import logging

router = APIRouter()
logger = logging.getLogger("llm_endpoint")

# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(None, description="Optional user prompt for workout generation")

@router.post("/llm/create-workout")
async def create_workout(
    request_data: CreateWorkoutRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    logger.info("[llm/create-workout] Start - User: %s", current_user.id)
    try:
        # 1. Starte die zentrale LLM-Workflow-Funktion
        saved_workout = await run_workout_chain(
            user_id=current_user.id,
            user_prompt=request_data.prompt,
            db=db,
            save_to_db=True
        )
        logger.info("[llm/create-workout] Workout gespeichert mit ID: %s", saved_workout.id)
        return {
            "success": True,
            "message": "Workout erfolgreich erstellt und in der Datenbank gespeichert.",
            "data": {"workout_id": saved_workout.id}
        }
    except HTTPException as he:
        logger.error("[llm/create-workout] HTTPException: %s", he.detail)
        raise
    except Exception as e:
        logger.error("[llm/create-workout] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Workout-Erstellung: {str(e)}"
        ) 