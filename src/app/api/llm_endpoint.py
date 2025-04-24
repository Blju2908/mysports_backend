from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import json
from sqlmodel import Session, select
from app.llm.schemas.workout_generation_schema import TrainingPlanSchema, ActivityLogSchema
from app.llm.chains.workout_generation_chain import generate_workout
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.models.training_plan_model import TrainingPlan

router = APIRouter()

@router.post("/llm/run")
def run_llm():
    try:
        # Beispiel-Daten laden (wie im Test)
        base_path = Path(__file__).parent.parent / "llm" / "examples"
        with open(base_path / "training_plan_example.json", "r", encoding="utf-8") as f:
            training_plan_data = json.load(f)
        training_plan = TrainingPlanSchema(**training_plan_data)
        with open(base_path / "training_history_example.json", "r", encoding="utf-8") as f:
            training_history_data = json.load(f)
        if isinstance(training_history_data, list):
            training_history = [ActivityLogSchema(**entry) for entry in training_history_data]
        else:
            training_history = [ActivityLogSchema(**training_history_data)]
        # LLM-Chain ausführen
        generate_workout(training_plan, training_history)
        return {"success": True, "message": "LLM-Call erfolgreich angestoßen."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim LLM-Call: {str(e)}")

@router.post("/llm/create-workout")
async def create_workout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_session)
):
    try:
        # 1. Aktuellen Trainingsplan des Benutzers laden
        query = (
            select(TrainingPlan)
            .join(TrainingPlanFollower)
            .where(TrainingPlanFollower.user_id == current_user.id)
        )
        result = db.exec(query).first()
        
        if not result:
            raise HTTPException(
                status_code=404,
                detail="Kein Trainingsplan gefunden. Bitte erstelle zuerst einen Trainingsplan."
            )
        
        # 2. Trainingsplan in das LLM-Schema konvertieren
        training_plan_schema = TrainingPlanSchema(
            id=result.id,
            goal=result.goal,
            restrictions=result.restrictions,
            equipment=result.equipment,
            session_duration=result.session_duration,
            description=result.description
        )
        
        # 3. Leere Trainingshistorie erstellen
        training_history = []
        
        # 4. LLM-Chain ausführen
        workout_result = generate_workout(training_plan_schema, training_history)
        
        # speichere das workout in einer .txt Datei
        with open("workout.txt", "w", encoding="utf-8") as f:
            f.write(workout_result)
        
        # 5. Erfolgreiche Antwort zurückgeben
        return {
            "success": True,
            "message": "Workout erfolgreich erstellt.",
            "data": workout_result
        }
    except HTTPException:
        raise  # Bereits formatierte HTTP-Fehler weiterleiten
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Workout-Erstellung: {str(e)}"
        ) 