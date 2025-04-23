from fastapi import APIRouter, HTTPException
from pathlib import Path
import json
from app.llm.schemas.workout_generation_schema import TrainingPlanSchema, ActivityLogSchema
from app.llm.chains.workout_generation_chain import generate_workout

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