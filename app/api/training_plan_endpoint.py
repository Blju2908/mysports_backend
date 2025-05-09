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

        user_id_uuid = UUID(current_user.id)
        # 2. Alte Verknüpfungen löschen
        db.exec(
            delete(TrainingPlanFollower).where(TrainingPlanFollower.user_id == user_id_uuid)
        )
        db.commit()

        # 3. Neue Verknüpfung User <-> Plan
        follower = TrainingPlanFollower(user_id=user_id_uuid, training_plan_id=plan.id)
        db.add(follower)
        db.commit()
        db.refresh(follower)

        # 4. Response sauber zurückgeben
        return APIResponse(
            success=True,
            data=TrainingPlanSchema.model_validate(plan),
            message="Trainingsplan erfolgreich erstellt."
        )
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
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user_in_db = result.scalar_one_or_none()
        
        
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
            new_follower_data = {"user_id": user_uuid, "training_plan_id": empty_plan.id}
            new_follower = TrainingPlanFollower(**new_follower_data)
            db.add(new_follower)
            await db.commit()
            return TrainingPlanSchema.model_validate(empty_plan)

        plan_query = select(TrainingPlan).where(TrainingPlan.id == follower.training_plan_id)
        plan_result = await db.exec(plan_query)
        plan = plan_result.first()

        if not plan:
            empty_plan = TrainingPlan(goal="", restrictions="", equipment="", session_duration="")
            db.add(empty_plan)
            await db.commit()
            await db.refresh(empty_plan)
            new_follower_data = {"user_id": user_uuid, "training_plan_id": empty_plan.id}
            new_follower = TrainingPlanFollower(**new_follower_data)
            db.add(new_follower)
            await db.commit()
            return TrainingPlanSchema.model_validate(empty_plan)

        return TrainingPlanSchema.model_validate(plan)
    except Exception as e:
        logger.error(f"[Get][Exception] {e}")
        logger.error(f"[Get][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden des Trainingsplans: {e}")


@router.put("/mine", response_model=TrainingPlanSchema)
async def update_my_training_plan(
    plan_data: TrainingPlanSchema = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    try:
        user_uuid = UUID(current_user.id)
        follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == user_uuid)
        result = await db.exec(follower_query)
        follower = result.first()

        plan_to_update: TrainingPlan
        if not follower or not follower.training_plan_id:
            # Wenn kein Plan existiert, lege einen neuen an
            new_plan = TrainingPlan(**plan_data.model_dump(exclude_unset=True))
            db.add(new_plan)
            await db.commit()
            await db.refresh(new_plan)
            
            new_follower_data = {"user_id": user_uuid, "training_plan_id": new_plan.id}
            new_follower = TrainingPlanFollower(**new_follower_data)
            db.add(new_follower)
            await db.commit()
            await db.refresh(new_follower)
            plan_to_update = new_plan
        else:
            retrieved_plan = await db.get(TrainingPlan, follower.training_plan_id)
            if not retrieved_plan:
                # Wenn Plan nicht gefunden, lege einen neuen an basierend auf input
                new_plan = TrainingPlan(**plan_data.model_dump(exclude_unset=True))
                db.add(new_plan)
                await db.commit()
                await db.refresh(new_plan)
                # Update follower to point to the new plan
                follower.training_plan_id = new_plan.id
                db.add(follower) # Add updated follower to session
                await db.commit()
                await db.refresh(follower)
                plan_to_update = new_plan
            else:
                plan_to_update = retrieved_plan
                # Update existing plan
                update_data = plan_data.model_dump(exclude_unset=True)
                for key, value in update_data.items():
                    setattr(plan_to_update, key, value)
                db.add(plan_to_update)
                await db.commit()
                await db.refresh(plan_to_update)

        logger.info(f"[Update] Updated/Created plan {plan_to_update.id} for user {user_uuid}")
        return TrainingPlanSchema.model_validate(plan_to_update)
    except Exception as e:
        await db.rollback()
        logger.error(f"[Update][Exception] {e}")
        logger.error(f"[Update][Exception] plan_data: {plan_data}")
        logger.error(f"[Update][Exception] current_user: {current_user}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren des Trainingsplans: {e}")