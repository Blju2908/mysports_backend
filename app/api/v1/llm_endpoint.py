from fastapi import APIRouter, HTTPException, Depends, Request
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.llm.workout_generation.create_workout_service import run_workout_chain
from app.services.llm_logging_service import log_workout_creation
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
import logging


router = APIRouter()
logger = logging.getLogger("llm_endpoint")


# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(None, description="Optional user prompt for workout generation")
    use_exercise_filtering: bool = Field(False, description="Enable exercise filtering based on user equipment and experience")
    approach: str = Field("two_step", description="Generation approach: 'one_step' or 'two_step'")
    
    @validator('approach')
    def validate_approach(cls, v):
        if v not in ["one_step", "two_step"]:
            raise ValueError("approach must be either 'one_step' or 'two_step'")
        return v


@router.post("/llm/create-workout")
async def create_workout(
    request_data: CreateWorkoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    logger.info("[llm/create-workout] Start - User: %s, Exercise Filtering: %s, Approach: %s", 
                current_user.id, request_data.use_exercise_filtering, request_data.approach)
    
    # Prepare request data for logging
    request_log_data = {
        "prompt": request_data.prompt,
        "user_id": current_user.id,
        "use_exercise_filtering": request_data.use_exercise_filtering,
        "approach": request_data.approach
    }
    
    async with await log_workout_creation(
        db=db, 
        user=current_user, 
        request=request,
        request_data=request_log_data
    ) as call_logger:
        try:
            # 1. Starte die zentrale LLM-Workflow-Funktion
            saved_workout = await run_workout_chain(
                user_id=current_user.id,
                user_prompt=request_data.prompt,
                db=db,
                save_to_db=True,
                use_exercise_filtering=request_data.use_exercise_filtering,
                approach="one_step"
            )
            
            # Store workout ID immediately to avoid lazy-loading issues
            workout_id = saved_workout.id
            logger.info("[llm/create-workout] Workout gespeichert mit ID: %s", workout_id)
            
            # Log success
            await call_logger.log_success(
                http_status_code=200,
                response_summary=f"Workout created successfully with ID: {workout_id}"
            )
            
            return {
                "success": True,
                "message": "Workout erfolgreich erstellt und in der Datenbank gespeichert.",
                "data": {"workout_id": workout_id}
            }
        except HTTPException as he:
            logger.error("[llm/create-workout] HTTPException: %s", he.detail)
            # Log error wird automatisch durch den Context Manager gemacht
            raise
        except Exception as e:
            logger.error("[llm/create-workout] Exception: %s", str(e), exc_info=True)
            # Log error wird automatisch durch den Context Manager gemacht
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler bei der Workout-Erstellung: {str(e)}"
            )