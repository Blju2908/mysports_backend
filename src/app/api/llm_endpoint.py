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
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from app.models.enums import BlockStatus
from datetime import datetime

router = APIRouter()

def save_workout_to_db(workout_schema, training_plan_id: int, db: Session) -> Workout:
    """
    Speichert das generierte Workout in der Datenbank und gibt das gespeicherte Workout-Objekt zurück.
    """
    # 1. Workout erstellen
    workout_db = Workout(
        training_plan_id=training_plan_id,
        name=workout_schema.name,
        date=workout_schema.date
    )
    db.add(workout_db)
    db.flush()  # Flush um die ID zu bekommen
    
    # 2. Blocks erstellen
    if workout_schema.blocks:
        for block_schema in workout_schema.blocks:
            block_db = Block(
                workout_id=workout_db.id,
                name=block_schema.name,
                description=block_schema.description,
                status=block_schema.status
            )
            db.add(block_db)
            db.flush()  # Flush um die ID zu bekommen
            
            # 3. Exercises erstellen
            if block_schema.exercises:
                for exercise_schema in block_schema.exercises:
                    exercise_db = Exercise(
                        block_id=block_db.id,
                        name=exercise_schema.name,
                        description=exercise_schema.description
                    )
                    db.add(exercise_db)
                    db.flush()  # Flush um die ID zu bekommen
                    
                    # 4. Sets erstellen
                    if exercise_schema.sets:
                        for set_schema in exercise_schema.sets:
                            set_db = Set(
                                exercise_id=exercise_db.id,
                                weight=set_schema.weight,
                                reps=set_schema.reps,
                                duration=set_schema.duration,
                                distance=set_schema.distance,
                                speed=set_schema.speed,
                                rest_time=set_schema.rest_time
                            )
                            db.add(set_db)
    
    # Commit the transaction
    db.commit()
    db.refresh(workout_db)
    return workout_db

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
        
        # 5. Workout in die Datenbank speichern
        saved_workout = save_workout_to_db(workout_result, result.id, db)
        
        # 6. Erfolgreiche Antwort zurückgeben
        return {
            "success": True,
            "message": "Workout erfolgreich erstellt und in der Datenbank gespeichert.",
            "data": {"workout_id": saved_workout.id}
        }
    except HTTPException:
        raise  # Bereits formatierte HTTP-Fehler weiterleiten
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler bei der Workout-Erstellung: {str(e)}"
        ) 