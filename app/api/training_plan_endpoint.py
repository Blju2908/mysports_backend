from fastapi import APIRouter, Depends, status, HTTPException, Body
from sqlmodel import Session, delete, select
from app.models.training_plan_model import TrainingPlan
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema, APIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from app.models.user_model import UserModel
import json

router = APIRouter(tags=["training-plan"])

logger = logging.getLogger("training_plan")


    

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_training_plan(
    plan_data: TrainingPlanSchema,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        # 1. Trainingsplan anlegen
        plan = TrainingPlan(**plan_data.model_dump())
        db.add(plan)
        db.commit()
        db.refresh(plan)  # Holt alle Felder inkl. id
        logger.info(f"[Create] Created plan: {plan}")

        # 2. Alte Verknüpfungen löschen
        db.exec(
            delete(TrainingPlanFollower).where(TrainingPlanFollower.user_id == current_user.id)
        )
        db.commit()

        # 3. Neue Verknüpfung User <-> Plan
        follower = TrainingPlanFollower(user_id=current_user.id, training_plan_id=plan.id)
        db.add(follower)
        db.commit()

        # 4. Response sauber zurückgeben
        return {
            "success": True,
            "data": plan,
            "message": "Trainingsplan erfolgreich erstellt."
        }
    except Exception as e:
        logger.error(f"[Create][Exception] {e}")
        logger.error(f"[Create][Exception] plan_data: {plan_data}")
        logger.error(f"[Create][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Erstellen des Trainingsplans: {e}")


@router.get("/mine", response_model=TrainingPlanSchema)
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(current_user.id)
        # Sicherstellen, dass der User in der eigenen Tabelle existiert
        user_in_db = await db.get(UserModel, user_uuid)
        if not user_in_db:
            new_user = UserModel(id=user_uuid)
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)

        follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == user_uuid)
        result = await db.exec(follower_query)
        follower = result.first()

        if not follower or not follower.training_plan_id:
            empty_plan = TrainingPlan(goal="", restrictions="", equipment="", session_duration="")
            db.add(empty_plan)
            await db.commit()
            await db.refresh(empty_plan)
            new_follower = TrainingPlanFollower(user_id=user_uuid, training_plan_id=empty_plan.id)
            db.add(new_follower)
            await db.commit()
            return empty_plan

        plan_query = select(TrainingPlan).where(TrainingPlan.id == follower.training_plan_id)
        plan_result = await db.exec(plan_query)
        plan = plan_result.first()

        if not plan:
            empty_plan = TrainingPlan(goal="", restrictions="", equipment="", session_duration="")
            db.add(empty_plan)
            await db.commit()
            await db.refresh(empty_plan)
            new_follower = TrainingPlanFollower(user_id=user_uuid, training_plan_id=empty_plan.id)
            db.add(new_follower)
            await db.commit()
            return empty_plan

        return plan
    except Exception as e:
        logger.error(f"[Get][Exception] {e}")
        logger.error(f"[Get][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Trainingsplans: {e}")


@router.put("/mine")
async def update_my_training_plan(
    plan_data: dict = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(current_user.id)
        follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == user_uuid)
        result = await db.exec(follower_query)
        follower = result.first()

        if not follower or not follower.training_plan_id:
            # Wenn kein Plan existiert, lege einen neuen an
            new_plan = TrainingPlan(goal="", restrictions="", equipment="", session_duration="")
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            new_follower = TrainingPlanFollower(user_id=user_uuid, training_plan_id=new_plan.id)
            db.add(new_follower)
            await db.commit()
            return new_plan

        plan_to_update = await db.get(TrainingPlan, follower.training_plan_id)

        if not plan_to_update:
            # Wenn Plan nicht gefunden, lege einen neuen an
            new_plan = TrainingPlan(goal="", restrictions="", equipment="", session_duration="")
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            new_follower = TrainingPlanFollower(user_id=user_uuid, training_plan_id=new_plan.id)
            db.add(new_follower)
            await db.commit()
            return new_plan

        # Überschreibe das Feld 'goal' mit dem JSON-String
        plan_to_update.goal = plan_data.get("goal", "")
        plan_to_update.restrictions = plan_data.get("restrictions", "")
        plan_to_update.equipment = plan_data.get("equipment", "")
        plan_to_update.session_duration = plan_data.get("session_duration", "")
        
        db.add(plan_to_update)
        
        await db.commit()
        await db.refresh(plan_to_update)
        logger.info(f"[Update] Updated plan {plan_to_update.id} for user {user_uuid}")
        return plan_to_update
    except Exception as e:
        logger.error(f"[Update][Exception] {e}")
        logger.error(f"[Update][Exception] plan_data: {plan_data}")
        logger.error(f"[Update][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren des Trainingsplans: {e}")