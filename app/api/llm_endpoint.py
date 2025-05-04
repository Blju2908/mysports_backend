from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.llm.chains.workout_generation_chain import generate_workout
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.models.training_plan_model import TrainingPlan
from app.models.training_history import ActivityLog
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
import logging
from app.services.workout_service import save_workout_to_db_async

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
        # 1. Aktuellen Trainingsplan des Benutzers laden
        query = (
            select(TrainingPlan)
            .join(TrainingPlanFollower)
            .where(TrainingPlanFollower.user_id == current_user.id)
        )
        result = await db.exec(query)
        trainings_plan = result.first()
        logger.info("[llm/create-workout] Trainingsplan: %s", trainings_plan)
        
        if not trainings_plan:
            logger.warning("[llm/create-workout] Kein Trainingsplan gefunden für User: %s", current_user.id)
            raise HTTPException(
                status_code=404,
                detail="Kein Trainingsplan gefunden. Bitte erstelle zuerst einen Trainingsplan."
            )
        
        # 3. Letzte 100 Einträge der Trainingshistorie des Users laden
        history_query = (
            select(ActivityLog)
            .where(ActivityLog.user_id == current_user.id)
            .order_by(ActivityLog.timestamp.desc())
            .limit(100)
        )
        history_result = await db.exec(history_query)
        training_history = history_result.all()
        logger.info("[llm/create-workout] Training History Count: %d", len(training_history))
        
        # Access the user prompt from the request body
        user_prompt = request_data.prompt
        logger.info("[llm/create-workout] User Prompt: %s", user_prompt)
        
        # 4. LLM-Chain ausführen (übergibt nun die geladene Historie und den Prompt)
        logger.info("[llm/create-workout] Starte LLM-Generierung...")
        workout_result = await generate_workout(trainings_plan, training_history, user_prompt)
        logger.info("[llm/create-workout] LLM-Generierung abgeschlossen.")
        
        # 5. Workout in die Datenbank speichern (Servicefunktion)
        logger.info("[llm/create-workout] Speichere Workout in DB (Service)...")
        saved_workout = await save_workout_to_db_async(
            workout_schema=workout_result,
            training_plan_id=trainings_plan.id,
            db=db
        )
        logger.info("[llm/create-workout] Workout gespeichert mit ID: %s", saved_workout.id)
        
        # 6. Erfolgreiche Antwort zurückgeben
        return {
            "success": True,
            "message": "Workout erfolgreich erstellt und in der Datenbank gespeichert.",
            "data": {"workout_id": saved_workout.id}
        }
    except HTTPException as he:
        logger.error("[llm/create-workout] HTTPException: %s", he.detail)
        raise  # Bereits formatierte HTTP-Fehler weiterleiten
    except Exception as e:
        logger.error("[llm/create-workout] Exception: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Workout-Erstellung: {str(e)}"
        ) 