from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from ..schemas.workout_generation_schema import (
    TrainingPlanSchema,
    ActivityLogSchema,
    WorkoutSchema,
)
from ..utils.langchain_utils import load_prompt
import json
import os

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
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    
    llm = ChatOpenAI(
        model="gpt-4.1",
        api_key=OPENAI_API_KEY,
        model_kwargs={"response_format": {"type": "json_object"}},
    )
    
    chain = ChatPromptTemplate.from_template("{prompt}") | llm
    
    response = chain.invoke({"prompt": prompt})
    
    # Debug: Gib die rohe LLM-Antwort aus und speichere sie in eine Datei
    output_path = "llm_output.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(response.content)
    print("LLM Output wurde in llm_output.txt gespeichert.")

    # LLM-Antwort als WorkoutSchema parsen
    workout = WorkoutSchema.model_validate_json(response.content)
    # Speichere das JSON in eine Datei
    with open("workout_output.json", "w", encoding="utf-8") as f:
        f.write(workout.model_dump_json(indent=2))
    print("Workout-JSON wurde in workout_output.json gespeichert.")
    return workout
