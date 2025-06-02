from fastapi import APIRouter, HTTPException, Depends, Request
from sqlmodel import select
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.llm.workout_generation.create_workout_service import run_workout_chain
from app.llm.training_plan_generation.training_plan_generation_service import run_training_plan_generation
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel
from app.schemas.training_plan_schema import TrainingPlanSchema # Für die Response
from app.services.llm_logging_service import log_workout_creation, log_training_principles_creation
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from typing import Dict, Any, List, Optional # Hinzugefügt für den Response-Typ
from datetime import datetime, date # Added for date conversion
import json

# JSON-Encoder für date-Objekte
class DateEncoder(json.JSONEncoder):
    """JSON-Encoder, der date-Objekte automatisch in ISO-Format-Strings umwandelt."""
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)

router = APIRouter()
logger = logging.getLogger("llm_endpoint")

# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(None, description="Optional user prompt for workout generation")

# Define a Pydantic model for the training plan request from frontend
class TrainingPlanRequest(BaseModel):
    id: Optional[int] = None
    gender: Optional[str] = None
    birthdate: Optional[str] = None
    height: Optional[float] = None
    weight: Optional[float] = None
    goal_types: Optional[List[str]] = None
    goal_details: Optional[str] = None
    fitness_level: Optional[int] = None
    experience_level: Optional[int] = None
    training_frequency: Optional[int] = None
    session_duration: Optional[int] = None
    equipment: Optional[List[str]] = None
    equipment_details: Optional[str] = None
    include_cardio: Optional[bool] = None
    restrictions: Optional[str] = None
    mobility_restrictions: Optional[str] = None
    training_principles: Optional[str] = None

@router.post("/llm/create-workout")
async def create_workout(
    request_data: CreateWorkoutRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    logger.info("[llm/create-workout] Start - User: %s", current_user.id)
    
    # Prepare request data for logging
    request_log_data = {
        "prompt": request_data.prompt,
        "user_id": current_user.id
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
                save_to_db=True
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

@router.post("/llm/create-training-principles", response_model=Dict[str, Any])
async def create_training_principles_endpoint(
    training_plan_data: TrainingPlanRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session)
):
    logger.info("[llm/create-training-principles] Start - User: %s", current_user.id)
    
    # Prepare request data for logging (without sensitive data)
    request_log_data = {
        "user_id": current_user.id,
        "has_training_plan_data": training_plan_data is not None,
        "goal_types": training_plan_data.goal_types if training_plan_data else None,
        "fitness_level": training_plan_data.fitness_level if training_plan_data else None
    }
    
    async with await log_training_principles_creation(
        db=db,
        user=current_user,
        request=request,
        request_data=request_log_data
    ) as call_logger:
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
                await db.commit()
                await db.refresh(user_db)

            # 2. Trainingsplan des Users laden oder erstellen
            training_plan = None
            if user_db.training_plan_id:
                plan_query = select(TrainingPlan).where(TrainingPlan.id == user_db.training_plan_id)
                plan_result = await db.execute(plan_query)
                training_plan = plan_result.scalar_one_or_none()
                
            if not training_plan:
                logger.info(f"[llm/create-training-principles] Creating new TrainingPlan for user {user_uuid}")
                training_plan = TrainingPlan()
                db.add(training_plan)
                await db.commit()
                await db.refresh(training_plan)
                
                # Verknüpfe User mit Plan
                user_db.training_plan_id = training_plan.id
                db.add(user_db)
                await db.commit()
                await db.refresh(user_db)

            # Update training_plan_id für Logging
            if call_logger.log_entry:
                call_logger.log_entry.training_plan_id = training_plan.id

            # 3. Update training plan with data from frontend
            update_dict = training_plan_data.model_dump(exclude_unset=True, exclude_none=True)
            
            # Handle date conversion for birthdate
            if 'birthdate' in update_dict and update_dict['birthdate']:
                try:
                    # Convert ISO string to date object
                    if isinstance(update_dict['birthdate'], str):
                        # Parse ISO format date string
                        dt = datetime.fromisoformat(update_dict['birthdate'].replace('Z', '+00:00'))
                        update_dict['birthdate'] = dt.date()
                        logger.info(f"[llm/create-training-principles] Converted birthdate from {training_plan_data.birthdate} to {update_dict['birthdate']}")
                except Exception as e:
                    logger.error(f"[llm/create-training-principles] Error converting birthdate: {e}")
                    # If conversion fails, remove birthdate to prevent DB errors
                    update_dict.pop('birthdate')
            
            for field, value in update_dict.items():
                if field != "id" and hasattr(training_plan, field):  # Skip id and check if field exists on model
                    setattr(training_plan, field, value)
            
            # Speichere Änderungen am Trainingsplan
            db.add(training_plan)
            await db.commit()
            await db.refresh(training_plan)
            
            # 4. Trainingsprinzipien generieren mit der überarbeiteten Funktion
            principles_schema = await run_training_plan_generation(
                user_id=user_uuid, 
                db=db
            )
            
            # 5. Trainingsprinzipien in Frontend-Format umwandeln und zurückgeben
            # Die Training-Plan-Daten sind bereits in der Datenbank aktualisiert
            await db.refresh(training_plan)  # Lade die neuesten Daten
            
            # Convert model to schema and then to frontend format
            response_schema = TrainingPlanSchema(**training_plan.model_dump())
            result = response_schema.to_frontend_format()
            
            # Log success
            await call_logger.log_success(
                http_status_code=200,
                response_summary=f"Training principles created successfully for training plan {training_plan.id}"
            )
            
            return result

        except HTTPException as he:
            logger.error("[llm/create-training-principles] HTTPException: %s", he.detail)
            await db.rollback() # Rollback bei Fehlern
            # Log error wird automatisch durch den Context Manager gemacht
            raise
        except ValueError as ve:
            logger.error(f"[llm/create-training-principles] ValueError: {str(ve)}")
            await db.rollback()
            # Log error wird automatisch durch den Context Manager gemacht
            # Wenn z.B. run_training_principles_chain einen Fehler wirft, weil kein Plan für den User existiert (obwohl wir hier einen erstellen)
            raise HTTPException(status_code=404, detail=str(ve))
        except Exception as e:
            logger.error("[llm/create-training-principles] Exception: %s", str(e), exc_info=True)
            await db.rollback()
            # Log error wird automatisch durch den Context Manager gemacht
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler bei der Erstellung der Trainingsprinzipien: {str(e)}"
            ) 