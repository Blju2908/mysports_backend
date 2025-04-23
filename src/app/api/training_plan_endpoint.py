from fastapi import APIRouter, Depends, status
from sqlmodel import Session, delete
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