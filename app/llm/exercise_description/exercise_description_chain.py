from langchain_openai import ChatOpenAI
from app.llm.exercise_description.exercise_description_schemas import ExerciseDescriptionSchema, MuscleGroup
from typing import List
from pathlib import Path
from pydantic import BaseModel, Field
import asyncio
import os
import json

PROMPT_FILE = "exercise_description_prompt.md"
OUTPUT_FILE = Path(__file__).parent / "output" / "exercise_descriptions.json"

class ExerciseBatchResponse(BaseModel):
    """Response schema für einen Batch von Übungsbeschreibungen"""
    exercises: List[ExerciseDescriptionSchema] = Field(..., description="Liste der beschriebenen Übungen")

async def check_existing_exercises(exercise_names: List[str]) -> List[str]:
    """
    Prüft welche Übungen bereits in der lokalen JSON-Datei existieren (basierend auf englischem Namen).
    
    Args:
        exercise_names: Liste der zu prüfenden Übungsnamen (deutsch)
    
    Returns:
        Liste der Übungen, die noch NICHT in der JSON-Datei sind
    """
    try:
        # Lade die aktuelle JSON-Datei falls vorhanden
        existing_from_json = set()
        if OUTPUT_FILE.exists():
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_from_json = {ex.get("name_english") for ex in data if ex.get("name_english")}
                else:
                    existing_from_json = {ex.get("name_english") for ex in data.get("exercises", []) if ex.get("name_english")}
            
            print(f"📄 Found {len(existing_from_json)} exercises in JSON file")
        else:
            print("📄 No existing JSON file found - will create new one")
        
        # Einfache Mappings für bekannte Übungen (deutsch -> englisch)
        simple_mappings = {
            "Bankdrücken": "Bench Press",
            "Kniebeugen": "Squat", 
            "Kreuzheben": "Deadlift",
            "Klimmzüge": "Pull-Ups",
            "Schulterdrücken": "Overhead Press",
            "Bizeps Curls": "Biceps Curls",
            "Trizeps Dips": "Triceps Dips",
            "Ausfallschritte": "Lunges",
            "Plank": "Plank",
            "Burpees": "Burpees",
            "Liegestütze": "Push-Ups",
            "Rudern": "Rows",
            "Seitheben": "Lateral Raises",
            "Frontheben": "Front Raises",
            "Reverse Flys": "Reverse Flys",
            "Wadenheben": "Calf Raises",
            "Beincurls": "Leg Curls",
            "Beinstrecker": "Leg Extensions",
            "Beinpresse": "Leg Press",
            "Latzug": "Lat Pulldown"
        }
        
        new_exercises = []
        filtered_count = 0
        
        for exercise_name in exercise_names:
            # Versuche zuerst die Mapping-Tabelle, dann den deutschen Namen als Fallback
            english_name = simple_mappings.get(exercise_name, exercise_name)
            if english_name not in existing_from_json:
                new_exercises.append(exercise_name)
            else:
                filtered_count += 1
                print(f"⏭️ Skipping existing exercise: {exercise_name} ({english_name})")
        
        print(f"✅ Filtered out {filtered_count} existing exercises")
        print(f"🆕 {len(new_exercises)} new exercises to process")
        
        return new_exercises
        
    except Exception as e:
        print(f"⚠️ Error checking existing exercises: {e}")
        # Bei Fehler: alle Übungen verarbeiten
        return exercise_names

async def save_exercises_to_json(exercises: List[ExerciseDescriptionSchema]):
    """
    Speichert Übungen in die feste JSON-Datei (append oder create).
    
    Args:
        exercises: Liste der neuen Übungen
    """
    # Erstelle Output-Verzeichnis falls nicht vorhanden
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    
    # Lade existierende Daten
    existing_exercises = []
    if OUTPUT_FILE.exists():
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
                # Handle both formats: direct list or object with exercises key
                if isinstance(existing_data, list):
                    existing_exercises = existing_data
                else:
                    existing_exercises = existing_data.get("exercises", [])
        except Exception as e:
            print(f"⚠️ Error reading existing JSON: {e}")
            existing_exercises = []
    
    # Füge neue Übungen hinzu
    new_exercises_data = [exercise.model_dump() for exercise in exercises]
    all_exercises = existing_exercises + new_exercises_data
    
    # Entferne Duplikate basierend auf englischem Namen
    seen_english_names = set()
    unique_exercises = []
    for exercise in all_exercises:
        english_name = exercise.get("name_english")
        if english_name and english_name not in seen_english_names:
            seen_english_names.add(english_name)
            unique_exercises.append(exercise)
    
    # Speichere als einfaches Array
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(unique_exercises, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved {len(unique_exercises)} total exercises to {OUTPUT_FILE}")

async def generate_exercise_descriptions_batch(exercise_names: List[str]) -> List[ExerciseDescriptionSchema]:
    """
    Generiert Übungsbeschreibungen für einen Batch von Übungen mit OpenAI O4-mini und structured output.
    
    Args:
        exercise_names: Liste der Übungsnamen für diesen Batch
    
    Returns:
        Liste von ExerciseDescriptionSchema mit den generierten Beschreibungen
    """
    if not exercise_names:
        return []
    
    print(f"🤖 Processing batch of {len(exercise_names)} exercises...")
    
    # Lade das Prompt Template
    prompt_path = Path(__file__).parent / PROMPT_FILE
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template_content = f.read()
    
    # Erstelle die Übungsliste für den Prompt
    exercise_list = "\n".join([f"- {name}" for name in exercise_names])
    
    # Formatiere den Prompt
    formatted_prompt = prompt_template_content.format(exercise_list=exercise_list)
    
    # API Key direkt aus Environment Variable holen
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY2 environment variable is not set")
    
    # OpenAI O4-mini mit Medium Reasoning konfigurieren
    reasoning = {
        "effort": "medium", 
        "summary": None
    }
    
    # llm = ChatOpenAI(
    #     model="o4-mini",
    #     api_key=OPENAI_API_KEY,
    #     use_responses_api=True,
    #     model_kwargs={"reasoning": reasoning}
    # )

    llm = ChatOpenAI(
        model="gpt-4.1",
        api_key=OPENAI_API_KEY,
        use_responses_api=True,
    )

    # Structured Output nach Langchain Best Practices
    structured_llm = llm.with_structured_output(ExerciseBatchResponse)
    
    print("🔄 Sending request to OpenAI O4-mini with structured output...")
    
    try:
        # API Call mit structured output
        response = await structured_llm.ainvoke(formatted_prompt)
        
        print(f"✅ Successfully generated {len(response.exercises)} exercise descriptions")
        return response.exercises
        
    except Exception as e:
        print(f"❌ Error in batch processing: {e}")
        import traceback
        traceback.print_exc()
        return []

async def generate_exercise_descriptions_with_batching(
    exercise_names: List[str], 
    batch_size: int = 10,
    delay_between_batches: float = 2.0
) -> List[ExerciseDescriptionSchema]:
    """
    Verarbeitet eine große Liste von Übungen in Batches und sammelt alle Ergebnisse.
    
    Args:
        exercise_names: Komplette Liste aller Übungsnamen
        batch_size: Anzahl Übungen pro Batch
        delay_between_batches: Pause zwischen Batches in Sekunden
    
    Returns:
        Komplette Liste aller ExerciseDescriptionSchema
    """
    if not exercise_names:
        return []
    
    # Entferne Duplikate und behalte die Reihenfolge
    unique_exercises = list(dict.fromkeys(exercise_names))
    
    print(f"🏋️ Processing {len(unique_exercises)} unique exercises...")
    if len(unique_exercises) != len(exercise_names):
        print(f"📝 Removed {len(exercise_names) - len(unique_exercises)} duplicates")
    
    # Prüfe welche Übungen bereits in der JSON-Datei existieren
    filtered_exercises = await check_existing_exercises(unique_exercises)
    
    if not filtered_exercises:
        print("✅ All exercises already exist in JSON file!")
        return []
    
    # Teile die gefilterten Übungen in Batches auf
    batches = [
        filtered_exercises[i:i + batch_size] 
        for i in range(0, len(filtered_exercises), batch_size)
    ]
    
    total_batches = len(batches)
    all_exercises = []
    
    print(f"📊 Processing {total_batches} batches (batch size: {batch_size})")
    
    for i, batch_exercises in enumerate(batches, 1):
        print(f"🔄 Processing batch {i}/{total_batches}...")
        
        try:
            # Verarbeite den aktuellen Batch
            batch_results = await generate_exercise_descriptions_batch(batch_exercises)
            
            if batch_results:
                # Speichere sofort in JSON-Datei
                await save_exercises_to_json(batch_results)
                all_exercises.extend(batch_results)
            
            print(f"✅ Batch {i}/{total_batches} completed ({len(batch_results)} exercises)")
            
            # Pause zwischen Batches (außer beim letzten)
            if i < total_batches:
                print(f"⏱️ Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)
                
        except Exception as e:
            print(f"❌ Error processing batch {i}/{total_batches}: {e}")
            print(f"📝 Successfully processed: {len(all_exercises)} exercises so far")
            # Hier könnten wir entscheiden, ob wir weitermachen oder abbrechen
            # Für jetzt brechen wir ab
            break
    
    print(f"🎉 Completed processing! Total exercises generated: {len(all_exercises)}")
    return all_exercises 