from fastapi import APIRouter, HTTPException, Depends
from sqlmodel import select
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.llm.service.create_workout_service import run_workout_chain
from app.llm.service.create_training_principles_service import run_training_principles_chain
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel
from app.schemas.training_plan_schema import TrainingPlanSchema # Für die Response
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from typing import Dict, Any # Hinzugefügt für den Response-Typ

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

@router.post("/llm/create-training-principles", response_model=Dict[str, Any])
async def create_training_principles_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    logger.info("[llm/create-training-principles] Start - User: %s", current_user.id)
    try:
        user_uuid = UUID(current_user.id)

        # 1. User-Objekt aus der Datenbank laden (oder erstellen, falls nicht vorhanden)
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user_db = result.scalar_one_or_none()

        if not user_db:
            # Sollte idealerweise nicht passieren, wenn der User authentifiziert ist,
            # aber als Fallback oder für Testszenarien
            logger.warning(f"[llm/create-training-principles] User {user_uuid} not found in UserModel, creating.")
            user_db = UserModel(id=user_uuid)
            db.add(user_db)
            # Kein await db.commit() hier, wird später zusammen commited

        # 2. Trainingsplan des Users laden oder erstellen
        training_plan: TrainingPlan | None
        if user_db.training_plan_id:
            training_plan = await db.get(TrainingPlan, user_db.training_plan_id)
            if not training_plan:
                logger.warning(f"[llm/create-training-principles] TrainingPlan with ID {user_db.training_plan_id} not found, creating new one.")
                training_plan = TrainingPlan() # Standardwerte werden vom Modell genommen
                db.add(training_plan)
        else:
            logger.info(f"[llm/create-training-principles] No TrainingPlan ID for user {user_uuid}, creating new TrainingPlan.")
            training_plan = TrainingPlan() # Standardwerte werden vom Modell genommen
            db.add(training_plan)
        
        await db.flush() # Um eine ID für den neuen Plan zu bekommen, falls erstellt

        if not training_plan:
             # Dieser Fall sollte durch die obige Logik eigentlich nicht eintreten
            logger.error(f"[llm/create-training-principles] Critical error: training_plan is None for user {user_uuid} after attempting to load/create.")
            raise HTTPException(status_code=500, detail="Fehler beim Laden oder Erstellen des Trainingsplans.")

        # 3. Trainingsprinzipien generieren
        # Die run_training_principles_chain erwartet user_id (UUID) und db Session
        generated_principles_text = await run_training_principles_chain(
            user_id=user_uuid, 
            db=db
        )

        # 4. Generierte Prinzipien im Trainingsplan speichern
        training_plan.training_principles = generated_principles_text
        db.add(training_plan) # Stelle sicher, dass der Plan für das Update markiert ist

        # 5. User mit Trainingsplan verknüpfen, falls noch nicht geschehen oder Plan neu erstellt wurde
        if not user_db.training_plan_id or user_db.training_plan_id != training_plan.id:
            user_db.training_plan_id = training_plan.id
            db.add(user_db)

        await db.commit()
        await db.refresh(training_plan)
        if user_db: # Refresh user_db falls es modifiziert wurde
             await db.refresh(user_db)

        logger.info(f"[llm/create-training-principles] Trainingsprinzipien für User {user_uuid} erfolgreich erstellt und gespeichert.")

        # 6. Aktualisierten Trainingsplan im Frontend-Format zurückgeben
        # Die `to_frontend_format` Methode ist im TrainingPlanSchema definiert
        response_schema = TrainingPlanSchema(**training_plan.model_dump())
        return response_schema.to_frontend_format()

    except HTTPException as he:
        logger.error("[llm/create-training-principles] HTTPException: %s", he.detail)
        await db.rollback() # Rollback bei Fehlern
        raise
    except ValueError as ve:
        logger.error(f"[llm/create-training-principles] ValueError: {str(ve)}")
        await db.rollback()
        # Wenn z.B. run_training_principles_chain einen Fehler wirft, weil kein Plan für den User existiert (obwohl wir hier einen erstellen)
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error("[llm/create-training-principles] Exception: %s", str(e), exc_info=True)
        await db.rollback()
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Erstellung der Trainingsprinzipien: {str(e)}"
        ) 