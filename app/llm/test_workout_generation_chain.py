import json
from pathlib import Path
from .schemas.workout_generation_schema import TrainingPlanSchema, ActivityLogSchema
from .chains.workout_generation_chain import generate_workout

def load_example(filename: str):
    path = Path(__file__).parent / "examples" / filename
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def main():
    # Trainingsplan laden
    training_plan_data = load_example("training_plan_example.json")
    training_plan = TrainingPlanSchema(**training_plan_data)
    # Trainingshistorie laden
    training_history_data = load_example("training_history_example.json")
    # Falls Liste, sonst in Liste packen
    if isinstance(training_history_data, list):
        training_history = [ActivityLogSchema(**entry) for entry in training_history_data]
    else:
        training_history = [ActivityLogSchema(**training_history_data)]
    # Chain ausführen
    workout = generate_workout(training_plan, training_history)
    print("\n--- Generiertes Workout ---\n")
    print(workout)  # Direkte Ausgabe des Strings

if __name__ == "__main__":
    main() 