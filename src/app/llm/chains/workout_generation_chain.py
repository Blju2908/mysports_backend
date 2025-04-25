from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..schemas.workout_generation_schema import (
    TrainingPlanSchema,
    ActivityLogSchema,
    WorkoutSchema,
)
from ..utils.langchain_utils import load_prompt
import json
from app.core.config import get_config
from app.models.workout_model import WorkoutStatus
from datetime import datetime

PROMPT_FILE = "workout_generation_prompt.txt"

# LLM-Chain Funktion


def generate_workout(
    training_plan: TrainingPlanSchema, training_history: list[ActivityLogSchema]
) -> WorkoutSchema:
    prompt_template = load_prompt(PROMPT_FILE)
    output_schema = WorkoutSchema.model_json_schema()
    # Trainingshistorie als JSON-String (ggf. gekürzt für Prompt)
    training_history_json = json.dumps(
        [entry.model_dump() for entry in training_history], indent=2, default=str
    )
    prompt = prompt_template.format(
        training_plan=training_plan.model_dump_json(indent=2),
        training_history=training_history_json,
        output_schema=json.dumps(output_schema, indent=2, default=str),
    )
    
    # API key aus der config holen
    config = get_config()
    OPENAI_API_KEY = config.OPENAI_API_KEY2
    
    llm = ChatOpenAI(
        model="o4-mini",
        api_key=OPENAI_API_KEY,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    
    chain = ChatPromptTemplate.from_template("{prompt}") | llm
    
    response = chain.invoke({"prompt": prompt})

    # LLM-Antwort als JSON parsen
    response_json = json.loads(response.content)
    
    # Sicherstellen, dass der Workout-Status auf INCOMPLETE gesetzt ist
    response_json["status"] = WorkoutStatus.INCOMPLETE
    # Setze das Datum auf jetzt
    response_json["date"] = datetime.now().isoformat()
    
    # Konvertiertes JSON als WorkoutSchema parsen
    workout = WorkoutSchema.model_validate(response_json)
    
    # Speichere das JSON in eine Datei
    with open("workout_output.json", "w", encoding="utf-8") as f:
        f.write(workout.model_dump_json(indent=2))
    
    print("Workout-JSON wurde in workout_output.json gespeichert.")
    return workout
