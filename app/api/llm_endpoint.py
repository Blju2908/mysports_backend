from fastapi import APIRouter, HTTPException, Depends
from pathlib import Path
import json
from sqlmodel import Session, select
from app.llm.chains.workout_generation_chain import generate_workout
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.models.training_plan_follower_model import TrainingPlanFollower
from app.models.training_plan_model import TrainingPlan
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set
from datetime import datetime
from app.models.training_history import ActivityLog
from pydantic import BaseModel, Field

router = APIRouter()

# Define a Pydantic model for the request body
class CreateWorkoutRequest(BaseModel):
    prompt: str | None = Field(None, description="Optional user prompt for workout generation")

def save_workout_to_db(workout_schema, training_plan_id: int, db: Session) -> Workout:
    """
    Speichert das generierte Workout in der Datenbank und gibt das gespeicherte Workout-Objekt zurück.
    """
    # 1. Workout erstellen
    workout_db = Workout(
        training_plan_id=training_plan_id,
        name=workout_schema.name,
        date=workout_schema.date,
        description=workout_schema.description
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

@router.post("/llm/create-workout")
async def create_workout(
    request_data: CreateWorkoutRequest, # Use the Pydantic model for the body
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
        trainings_plan = db.exec(query).first()
        
        if not trainings_plan:
            raise HTTPException(
                status_code=404,
                detail="Kein Trainingsplan gefunden. Bitte erstelle zuerst einen Trainingsplan."
            )
        
        # 3. Letzte 100 Einträge der Trainingshistorie des Users laden
        history_query = (
            select(ActivityLog)
            .where(ActivityLog.user_id == current_user.id)
            .order_by(ActivityLog.timestamp.desc())
            .limit(100)
        )
        training_history = db.exec(history_query).all()
        
        # Access the user prompt from the request body
        user_prompt = request_data.prompt
        
        # TODO: Pass user_prompt to the LLM chain
        # For now, we just receive it. The actual LLM call modification
        # will be done in the next step.
        print(f"Received user prompt: {user_prompt}") # Example logging
        
        # 4. LLM-Chain ausführen (übergibt nun die geladene Historie)
        # Note: generate_workout currently does not accept user_prompt
        workout_result = generate_workout(trainings_plan, training_history)
        
        # 5. Workout in die Datenbank speichern
        saved_workout = save_workout_to_db(workout_result, trainings_plan.id, db)
        
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