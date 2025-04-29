from fastapi import APIRouter, Depends, status, HTTPException
from sqlmodel import Session, delete, select
from pydantic import BaseModel
from app.models.training_plan_model import TrainingPlan
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanResponse, APIResponse

router = APIRouter(tags=["training-plan"])

class TrainingPlanCreate(BaseModel):
    goal: str
    restrictions: str
    equipment: str
    session_duration: int
    description: str
    

@router.post("/", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_training_plan(
    plan_data: TrainingPlanCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    # 1. Trainingsplan anlegen
    plan = TrainingPlan(**plan_data.model_dump())
    db.add(plan)
    db.commit()
    db.refresh(plan)  # Holt alle Felder inkl. id

    print(plan)

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


@router.get("/mine", response_model=TrainingPlanResponse)
async def get_my_training_plan(
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Retrieves the training plan the current user is following.
    """
    # Find the follower entry for the current user
    follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == current_user.id)
    follower = db.exec(follower_query).first()

    if not follower or not follower.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found for this user."
        )

    # Retrieve the actual training plan
    plan_query = select(TrainingPlan).where(TrainingPlan.id == follower.training_plan_id)
    plan = db.exec(plan_query).first()

    if not plan:
        # This case should ideally not happen if follower entry exists, but good to handle
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training plan details not found."
        )

    return plan


@router.put("/mine", response_model=TrainingPlanResponse)
async def update_my_training_plan(
    plan_data: TrainingPlanCreate,
    db: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Updates the training plan the current user is following.
    """
    # Find the follower entry for the current user
    follower_query = select(TrainingPlanFollower).where(TrainingPlanFollower.user_id == current_user.id)
    follower = db.exec(follower_query).first()

    if not follower or not follower.training_plan_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active training plan found to update."
        )

    # Retrieve the actual training plan to update
    plan_to_update = db.get(TrainingPlan, follower.training_plan_id)

    if not plan_to_update:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training plan details not found for update."
        )

    # Update the plan fields
    update_data = plan_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(plan_to_update, key, value)

    db.add(plan_to_update)
    db.commit()
    db.refresh(plan_to_update)

    return plan_to_update