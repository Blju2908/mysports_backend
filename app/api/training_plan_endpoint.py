from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, delete, select
from app.models.training_plan_model import TrainingPlan
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema, APIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging

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
            logger.info(f"[Get] Created empty plan for user {user_uuid}: {empty_plan}")
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
            logger.info(f"[Get] Fallback: Created empty plan for user {user_uuid}: {empty_plan}")
            return empty_plan

        return plan
    except Exception as e:
        logger.error(f"[Get][Exception] {e}")
        logger.error(f"[Get][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Trainingsplans: {e}")


@router.put("/mine", response_model=TrainingPlanSchema)
async def update_my_training_plan(
    plan_data: TrainingPlanSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(current_user.id)
        follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == user_uuid)
        result = await db.exec(follower_query)
        follower = result.first()

        if not follower or not follower.training_plan_id:
            logger.warning(f"[Update] No active plan for user {user_uuid}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active training plan found to update."
            )

        plan_to_update = await db.get(TrainingPlan, follower.training_plan_id)

        if not plan_to_update:
            logger.warning(f"[Update] Plan not found for id {follower.training_plan_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Training plan details not found for update."
            )

        update_data = plan_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(plan_to_update, key, value)

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