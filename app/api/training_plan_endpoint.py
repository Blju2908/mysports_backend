from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlmodel import Session, select
from app.models.training_plan_model import TrainingPlan
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema, APIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from app.models.user_model import UserModel
from datetime import date
from typing import Optional, Dict, Any
import json
from pydantic import ValidationError

router = APIRouter(tags=["training-plan"])

logger = logging.getLogger("training_plan")


@router.get("/mine", response_model=Dict[str, Any])
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(current_user.id)
        # Sicherstellen, dass der User in der eigenen Tabelle existiert
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user_in_db = result.scalar_one_or_none()
        
        if not user_in_db:
            new_user = UserModel(id=user_uuid)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            user_in_db = new_user

        # Prüfe, ob der User einen Trainingsplan hat
        if not user_in_db.training_plan_id:
            # Erstelle einen leeren Trainingsplan mit Standardwerten
            empty_plan = TrainingPlan(
                equipment="",
                session_duration=45,
                training_frequency=3,
                fitness_level=3,
                experience_level=3,
                include_cardio=True
            )
            db.add(empty_plan)
            await db.commit()
            await db.refresh(empty_plan)
            
            # Verknüpfe User mit neuem Plan
            user_in_db.training_plan_id = empty_plan.id
            db.add(user_in_db)
            await db.commit()
            await db.refresh(user_in_db)
            
            # Konvertiere in Frontend-Format
            plan_dict = empty_plan.model_dump()
            schema = TrainingPlanSchema(**plan_dict)
            return schema.to_frontend_format()

        # Hole den Trainingsplan des Users
        plan_query = select(TrainingPlan).where(TrainingPlan.id == user_in_db.training_plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()

        if not plan:
            # Falls Plan nicht gefunden, erstelle einen neuen
            empty_plan = TrainingPlan(
                equipment="",
                session_duration=45,
                training_frequency=3,
                fitness_level=3,
                experience_level=3,
                include_cardio=True
            )
            db.add(empty_plan)
            await db.commit()
            await db.refresh(empty_plan)
            
            # Verknüpfe User mit neuem Plan
            user_in_db.training_plan_id = empty_plan.id
            db.add(user_in_db)
            await db.commit()
            await db.refresh(user_in_db)
            
            # Konvertiere in Frontend-Format
            plan_dict = empty_plan.model_dump()
            schema = TrainingPlanSchema(**plan_dict)
            return schema.to_frontend_format()

        # Konvertiere in Frontend-Format
        plan_dict = plan.model_dump()
        schema = TrainingPlanSchema(**plan_dict)
        return schema.to_frontend_format()
    except Exception as e:
        logger.error(f"[Get][Exception] {e}")
        logger.error(f"[Get][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Trainingsplans: {e}")


@router.put("/mine", response_model=dict)
async def update_my_training_plan(
    plan_data: dict = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # Log received data for debugging
        logger.info(f"[Update] Received raw update data: {plan_data}")
        
        # Konvertiere vom Frontend in Backend-Format
        schema_data = TrainingPlanSchema.from_frontend_format(plan_data)
        
        user_uuid = UUID(current_user.id)
        
        # Hole den User
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Erstelle User, falls nicht vorhanden
            user = UserModel(id=user_uuid)
            db.add(user)
            await db.commit()
            await db.refresh(user)

        # Prüfe, ob der Plan existiert und hole ihn oder erstelle einen neuen
        if not user.training_plan_id:
            logger.info(f"[Update] User {user_uuid} has no training plan, creating new one")
            # Erstelle einen leeren Plan
            new_plan = TrainingPlan()
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            
            # Verknüpfe mit User
            user.training_plan_id = new_plan.id
            db.add(user)
            await db.commit()
            await db.refresh(user)
            plan_to_update = new_plan
        else:
            # Versuche existierenden Plan zu laden
            plan_query = select(TrainingPlan).where(TrainingPlan.id == user.training_plan_id)
            plan_result = await db.execute(plan_query)
            existing_plan = plan_result.scalar_one_or_none()
            
            if not existing_plan:
                logger.info(f"[Update] Training plan ID {user.training_plan_id} not found for user {user_uuid}, creating new one")
                # Plan existiert nicht mehr, erstelle einen neuen
                new_plan = TrainingPlan()
                db.add(new_plan)
                await db.commit()
                await db.refresh(new_plan)
                
                # Update user reference
                user.training_plan_id = new_plan.id
                db.add(user)
                await db.commit()
                await db.refresh(user)
                plan_to_update = new_plan
            else:
                plan_to_update = existing_plan

        # Aktualisiere den Plan mit den neuen Daten
        logger.info(f"[Update] Updating plan {plan_to_update.id} with new data")
        update_data = schema_data.model_dump(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            # Don't update ID field
            if key != "id":
                setattr(plan_to_update, key, value)
        
        db.add(plan_to_update)
        await db.commit()
        await db.refresh(plan_to_update)

        logger.info(f"[Update] Successfully updated plan {plan_to_update.id} for user {user_uuid}")
        
        # Konvertiere zurück zum Frontend-Format
        plan_dict = plan_to_update.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        return response_schema.to_frontend_format()
    except ValidationError as ve:
        logger.error(f"[Update][ValidationError] {ve}")
        logger.error(f"[Update][ValidationError] Errors: {ve.errors()}")
        await db.rollback()
        raise HTTPException(
            status_code=422, 
            detail=f"Validierungsfehler: {ve.errors()}"
        )
    except Exception as e:
        await db.rollback()
        logger.error(f"[Update][Exception] {e}")
        logger.error(f"[Update][Exception] plan_data: {plan_data}")
        logger.error(f"[Update][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren des Trainingsplans: {e}")

@router.post("/mine/principles", response_model=dict)
async def generate_training_principles(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Generiert Trainingsprinzipien basierend auf dem Benutzerprofil.
    In dieser Version wird nur ein Platzhalter-Text zurückgegeben. 
    Die tatsächliche KI-Integration wird später implementiert.
    """
    try:
        user_uuid = UUID(current_user.id)
        
        # Hole den User und seinen Trainingsplan
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user or not user.training_plan_id:
            raise HTTPException(
                status_code=404, 
                detail="Kein Trainingsplan gefunden. Bitte fülle zuerst dein Trainingsprofil aus."
            )
            
        plan = await db.get(TrainingPlan, user.training_plan_id)
        if not plan:
            raise HTTPException(
                status_code=404, 
                detail="Trainingsplan nicht gefunden."
            )
            
        # Platzhalter für Trainingsprinzipien (später wird hier die OpenAI-Integration implementiert)
        plan.training_principles = """
        Dies sind deine personalisierten Trainingsprinzipien, basierend auf deinen Zielen und Einschränkungen:
        
        1. Progressive Belastungssteigerung: Erhöhe kontinuierlich die Trainingsintensität, um Adaptation zu fördern.
        2. Individuelle Anpassung: Das Training ist auf deine persönlichen Ziele und Voraussetzungen abgestimmt.
        3. Funktionelle Bewegungsmuster: Konzentration auf natürliche, alltagsrelevante Bewegungen.
        4. Ausgewogene Entwicklung: Balance zwischen Kraft, Ausdauer, Beweglichkeit und Koordination.
        5. Regeneration und Erholung: Ausreichende Erholungsphasen sind für deinen Trainingserfolg essenziell.
        
        Diese Prinzipien dienen als Grundlage für die Erstellung und Anpassung deines individuellen Trainingsplans.
        """
        
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Konvertiere ins Frontend-Format
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        return response_schema.to_frontend_format()
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Principles][Exception] {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Generierung der Trainingsprinzipien: {e}"
        )