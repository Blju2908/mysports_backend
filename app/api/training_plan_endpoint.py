# backend/app/api/training_plan_endpoint.py - OPTIMIZED VERSION
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import Dict, Any

router = APIRouter(tags=["training-plan"])


@router.get("/mine", response_model=TrainingPlanSchema)
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ BEST PRACTICE: Kombinierte Query + Auto-Creation falls nicht vorhanden
    """
    query = (
        select(UserModel, TrainingPlan)
        .outerjoin(TrainingPlan, UserModel.training_plan_id == TrainingPlan.id)
        .where(UserModel.id == UUID(current_user.id))
    )
    result = await db.execute(query)
    user_plan_tuple = result.first()
    
    if not user_plan_tuple:
        # User existiert nicht - erstellen mit leerem Plan
        user = UserModel(id=UUID(current_user.id))
        plan = TrainingPlan(
            equipment=[],
            workout_styles=[],
            session_duration=45,
            training_frequency=3,
            fitness_level=3,
            experience_level=3
        )
        db.add(plan)
        await db.flush()  # Plan ID bekommen
        
        user.training_plan_id = plan.id
        db.add(user)
        
        try:
            await db.commit()
            await db.refresh(plan)  # 🔧 WICHTIG: Frisch erstelltes Objekt laden!
            return TrainingPlanSchema.model_validate(plan)  # ✅ Auto-Serialization!
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating training plan: {str(e)}")
    
    user, plan = user_plan_tuple
    
    if not plan:
        # User existiert, aber kein Plan - Plan erstellen
        plan = TrainingPlan(
            equipment=[],
            workout_styles=[],
            session_duration=45,
            training_frequency=3,
            fitness_level=3,
            experience_level=3
        )
        db.add(plan)
        await db.flush()
        
        user.training_plan_id = plan.id
        db.add(user)
        
        try:
            await db.commit()
            await db.refresh(plan)  # 🔧 WICHTIG: Plan nach DB-Erstellung laden!
        except Exception as e:
            await db.rollback()
            raise HTTPException(status_code=500, detail=f"Error creating training plan: {str(e)}")
    
    return TrainingPlanSchema.model_validate(plan)  # ✅ Auto-Serialization!


@router.put("/mine", response_model=TrainingPlanSchema)
async def update_my_training_plan(
    plan_update: TrainingPlanSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    ✅ UPSERT: Erstellt oder updated TrainingPlan
    """
    # 🔥 UPSERT: OuterJoin um sowohl existierende als auch neue Pläne zu handhaben
    query = (
        select(UserModel, TrainingPlan)
        .outerjoin(TrainingPlan, UserModel.training_plan_id == TrainingPlan.id)
        .where(UserModel.id == UUID(current_user.id))
    )
    result = await db.execute(query)
    user_plan_tuple = result.first()
    
    if not user_plan_tuple:
        # User existiert nicht - erstellen mit Plan
        user = UserModel(id=UUID(current_user.id))
        plan = TrainingPlan()
        db.add(plan)
        await db.flush()  # Plan ID bekommen
        
        user.training_plan_id = plan.id
        db.add(user)
    else:
        user, plan = user_plan_tuple
        
        if not plan:
            # User existiert, aber kein Plan - Plan erstellen
            plan = TrainingPlan()
            db.add(plan)
            await db.flush()
            
            user.training_plan_id = plan.id
    
    # ✅ Update alle Felder aus dem Request
    update_data = plan_update.model_dump(exclude_unset=True, exclude={"id"})
    for field, value in update_data.items():
        setattr(plan, field, value)
    
    try:
        await db.commit()
        await db.refresh(plan)  # 🔧 WICHTIG: Objekt vollständig aus DB laden!
        return TrainingPlanSchema.model_validate(plan)  # ✅ Auto-Serialization!
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Error upserting training plan: {str(e)}")