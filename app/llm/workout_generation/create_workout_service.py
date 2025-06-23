from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List, Dict, Optional
import json
from pathlib import Path
from datetime import datetime

from app.db.trainingplan_db_access import get_training_plan_for_user
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.workout_generation_chain import generate_workout
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set

async def run_workout_chain(
    user_id: UUID | None,
    user_prompt: str | None,
    db: AsyncSession,
    save_to_db: bool = False,
) -> Any:
    """
    Führt den Workout-Generierungs-Prozess mit dem LLM durch.
    Lädt die letzten 10 Workouts des Users als Trainingshistorie.

    Args:
        user_id: Die ID des Benutzers.
        user_prompt: Ein optionaler Prompt des Benutzers.
        db: Die Datenbankverbindung.
        save_to_db: Wenn True, wird das Workout in der DB gespeichert und das Model zurückgegeben.
                    Wenn False, wird das generierte Workout als Dictionary (vom Pydantic Schema) zurückgegeben.

    Returns:
        Abhängig von `save_to_db`: das gespeicherte Workout-DB-Modell oder ein Dictionary des generierten Workouts.
    """

    formatted_training_plan = None
    training_plan_id_for_saving = None
    formatted_history = None

    if user_id is not None:
        # Get training plan from the user
        training_plan_db_obj = await get_training_plan_for_user(user_id, db)
        if training_plan_db_obj:
            training_plan_id_for_saving = training_plan_db_obj.id
            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

        # Get and format training history (last 10 workouts)
        raw_training_history: List[Workout] = (
            await get_training_history_for_user_from_db(user_id, db, limit=10)
        )
        
        if raw_training_history:
            formatted_history = format_training_history_for_llm(
                raw_training_history
            )
        
    # LLM-Call durchführen
    llm_output_schema = await generate_workout(
        training_plan=formatted_training_plan,
        training_history=formatted_history,
        user_prompt=user_prompt,
    )

    workout_model = convert_llm_output_to_db_models(
        llm_output_schema.model_dump(),
        training_plan_id=training_plan_id_for_saving,
    )

    if save_to_db:
        db.add(workout_model)
        await db.commit()
        await db.refresh(workout_model)
        print(
            f"Workout erfolgreich in Datenbank gespeichert mit ID: {workout_model.id}"
        )
        return workout_model
    else:
        # Return the raw Pydantic model output as a dict
        return llm_output_schema.model_dump()

def format_training_plan_for_llm(training_plan) -> str:
    """
    Formats the training plan data into a structured text format for the LLM.
    Converts all training plan attributes into readable sections.
    """
    sections = []
    
    # Personal Information
    personal_info = []
    if training_plan.gender:
        personal_info.append(f"Geschlecht: {training_plan.gender}")
    if training_plan.birthdate:
        from datetime import date
        age = date.today().year - training_plan.birthdate.year
        personal_info.append(f"Alter: {age} Jahre")
    if training_plan.height:
        personal_info.append(f"Körpergröße: {training_plan.height} cm")
    if training_plan.weight:
        personal_info.append(f"Gewicht: {training_plan.weight} kg")
    
    if personal_info:
        sections.append("## Persönliche Informationen\n" + "\n".join(personal_info))
    
    # Training Goals
    goals_info = []
    if training_plan.workout_styles:
        goals_info.append(f"Bevorzugter Workout Style: {', '.join(training_plan.workout_styles)}")
    if training_plan.goal_details:
        goals_info.append(f"Beschreibung: {training_plan.goal_details}")
    
    if goals_info:
        sections.append("## Trainingsziele\n" + "\n".join(goals_info))
    
    # Experience Level
    experience_info = []
    if training_plan.fitness_level is not None:
        fitness_labels = {
            1: "Sehr unfit", 
            2: "Unfit", 
            3: "Durchschnittlich", 
            4: "Fit", 
            5: "Sehr fit", 
            6: "Athletisch", 
            7: "Elite"
        }
        experience_info.append(f"Fitnesslevel: {fitness_labels.get(training_plan.fitness_level, training_plan.fitness_level)} ({training_plan.fitness_level}/7)")
    if training_plan.experience_level is not None:
        exp_labels = {
            1: "Anfänger", 
            2: "Wenig Erfahrung", 
            3: "Grundkenntnisse", 
            4: "Etwas Erfahrung", 
            5: "Erfahren", 
            6: "Sehr erfahren", 
            7: "Experte"
        }
        experience_info.append(f"Trainingserfahrung: {exp_labels.get(training_plan.experience_level, training_plan.experience_level)} ({training_plan.experience_level}/7)")
    
    if experience_info:
        sections.append("## Erfahrungslevel\n" + "\n".join(experience_info))
    
    # Training Schedule
    schedule_info = []
    if training_plan.training_frequency:
        schedule_info.append(f"Trainingsfrequenz: {training_plan.training_frequency}x pro Woche")
    if training_plan.session_duration:
        schedule_info.append(f"Trainingsdauer: {training_plan.session_duration} Minuten")
    if training_plan.other_regular_activities:
        schedule_info.append(f"Andere regelmäßige Aktivitäten: {training_plan.other_regular_activities}")
    
    if schedule_info:
        sections.append("## Trainingsplan\n" + "\n".join(schedule_info))
    
    # Equipment & Environment
    equipment_info = []
    if training_plan.equipment:
        # Directly use equipment values from database without separate mapping logic
        equipment_info.append(f"Standard Ausrüstung: {', '.join(training_plan.equipment)}")
    if training_plan.equipment_details:
        equipment_info.append(f"Zusätzliche Informationen: {training_plan.equipment_details}")
    
    if equipment_info:
        sections.append("## Equipment & Umgebung\n" + "\n".join(equipment_info))
    
    # Restrictions
    restrictions_info = []
    if training_plan.restrictions:
        restrictions_info.append(f"Verletzungen/Einschränkungen: {training_plan.restrictions}")
    if training_plan.mobility_restrictions:
        restrictions_info.append(f"Mobilitätseinschränkungen: {training_plan.mobility_restrictions}")
    
    if restrictions_info:
        sections.append("## Einschränkungen\n" + "\n".join(restrictions_info))
    
    # Comments
    if training_plan.comments:
        sections.append(f"## Zusätzliche Kommentare\n{training_plan.comments}")
    
    if not sections:
        return "Keine Trainingsplandaten verfügbar."
    
    return "\n\n".join(sections)

def format_training_history_for_llm(
    training_history_workouts: List[Workout],
) -> str | None:
    """
    Formats the training history into a structured JSON string suitable for the LLM.
    Focuses on when the user trained, their notes, and actual executed exercises.
    Only includes workouts that have at least one completed set.
    Optimized for information density: removes null/zero values, compresses identical sets, removes rest times.
    Returns None if no workouts are provided.
    """
    if not training_history_workouts:
        return None
    
    # Note: The workout history is already filtered by get_user_workout_history
    # to only include completed sets and their parent elements
    
    history_data = []
    
    for workout in training_history_workouts:
        # Find the earliest completed_at from sets as the workout completion date
        workout_completion_date_str = "N/A"
        earliest_completed_at = None
        
        for block in workout.blocks:
            for exercise in block.exercises:
                for s_set in exercise.sets:
                    if s_set.completed_at:
                        if earliest_completed_at is None or s_set.completed_at < earliest_completed_at:
                            earliest_completed_at = s_set.completed_at
                            
        if earliest_completed_at:
            workout_completion_date_str = earliest_completed_at.strftime("%Y-%m-%d")

        # Create workout object
        workout_obj = {
            "name": workout.name if workout.name else "Unnamed Workout",
            "date": workout_completion_date_str,
            "blocks": []
        }
        
        if workout.focus:
            workout_obj["focus"] = workout.focus
        if workout.duration:
            workout_obj["duration"] = workout.duration
        if workout.notes:
            workout_obj["notes"] = workout.notes
        
        # Add blocks
        for block in workout.blocks:
            block_obj = {
                "name": block.name if block.name else "Unnamed Block",
                "exercises": []
            }
            
            if block.notes:
                block_obj["notes"] = block.notes
            
            # Add exercises
            for exercise in block.exercises:
                exercise_obj = {
                    "name": exercise.name if exercise.name else "Unnamed Exercise",
                    "sets": []
                }
                
                if exercise.notes:
                    exercise_obj["notes"] = exercise.notes
                if exercise.superset_id:
                    exercise_obj["superset_id"] = exercise.superset_id
                
                # Collect and compress sets
                raw_sets = []
                for s in exercise.sets:
                    set_obj = {}
                    if s.weight is not None and s.weight != 0.0:
                        set_obj["weight"] = s.weight
                    if s.reps is not None and s.reps != 0:
                        set_obj["reps"] = s.reps
                    if s.duration is not None and s.duration != 0:
                        set_obj["duration"] = s.duration
                    if s.distance is not None and s.distance != 0.0:
                        set_obj["distance"] = s.distance
                    # Note: rest_time completely removed as requested
                    
                    if set_obj:  # Only add if there's at least one non-zero value
                        raw_sets.append(set_obj)
                
                # Compress identical sets (simple approach)
                if raw_sets:
                    compressed_sets = []
                    current_set = raw_sets[0]
                    count = 1
                    
                    for i in range(1, len(raw_sets)):
                        if raw_sets[i] == current_set:
                            count += 1
                        else:
                            # Add the compressed set
                            if count == 1:
                                compressed_sets.append(current_set)
                            else:
                                compressed_set = current_set.copy()
                                compressed_set["count"] = count
                                compressed_sets.append(compressed_set)
                            
                            # Start new group
                            current_set = raw_sets[i]
                            count = 1
                    
                    # Add the last group
                    if count == 1:
                        compressed_sets.append(current_set)
                    else:
                        compressed_set = current_set.copy()
                        compressed_set["count"] = count
                        compressed_sets.append(compressed_set)
                    
                    exercise_obj["sets"] = compressed_sets
                
                if exercise_obj.get("sets"):  # Only add if there's at least one set
                    block_obj["exercises"].append(exercise_obj)
            
            if block_obj["exercises"]:  # Only add if there's at least one exercise
                workout_obj["blocks"].append(block_obj)
        
        if workout_obj["blocks"]:  # Only add if there's at least one block
            history_data.append(workout_obj)

    if not history_data:
        return None

    # Convert to JSON string
    return json.dumps(history_data, ensure_ascii=False)

def convert_llm_output_to_db_models(
    workout_dict: Dict[str, Any],  # Expecting dict from WorkoutSchema.model_dump()
    training_plan_id: Optional[int] = None,
) -> Workout:
    """
    Konvertiert das LLM-Output (Pydantic Schema dict) in ein Workout-DB-Modell
    und zugehörige Block-, Exercise- und Set-Modelle.
    Die 'values' Liste in SetSchema wird in die plan_* Felder des Set-Modells gemappt.
    [weight, reps, duration, distance, rest_time]
    Akzeptiert auch explizite Felder (plan_weight, plan_reps, ...).

    Args:
        workout_dict: Das LLM-Output als Dict (von WorkoutSchema.model_dump()).
        training_plan_id: Optional die ID des Trainingsplans.

    Returns:
        Ein Workout-Modell mit allen Beziehungen.
    """
    # Erstelle das Workout-Modell
    workout_model = Workout(
        training_plan_id=training_plan_id,
        name=workout_dict.get("name", "Unbenanntes Workout"),
        description=workout_dict.get("description"),
        focus=workout_dict.get("focus"),
        duration=workout_dict.get("duration"),
        date_created=datetime.utcnow(),
        blocks=[],
    )

    for block_data in workout_dict.get("blocks", []):
        block_model = Block(
            name=block_data.get("name", "Unbenannter Block"),
            description=block_data.get("description"),
            exercises=[],
        )

        for exercise_data in block_data.get("exercises", []):
            exercise_model = Exercise(
                name=exercise_data.get("name", "Unbenannte Übung"),
                description=exercise_data.get("description"),
                superset_id=exercise_data.get("superset_id"),
                sets=[],
            )

            for set_data_from_llm in exercise_data.get("sets", []):
                set_obj = None
                if isinstance(set_data_from_llm, dict) and "values" in set_data_from_llm:
                    values = set_data_from_llm.get("values", [])
                    if not isinstance(values, list):
                        print(f"Skipping set data as 'values' is not a list: {values}")
                        continue

                    # Ensure values list has at least 5 elements, padding with None if shorter
                    padded_values = (values + [None] * 5)[:5]
                    
                    v_weight, v_reps, v_duration, v_distance, v_rest_time = padded_values

                    # Check if any numerical value is present or if notes are present
                    has_numerical_value = any(
                        val is not None for val in [v_weight, v_reps, v_duration, v_distance, v_rest_time]
                    )

                    if has_numerical_value:
                        set_obj = Set(
                            weight=float(v_weight) if v_weight is not None else None,
                            reps=int(v_reps) if v_reps is not None else None,
                            duration=int(v_duration) if v_duration is not None else None,
                            distance=float(v_distance) if v_distance is not None else None,
                            rest_time=int(v_rest_time) if v_rest_time is not None else None,
                        )
                    else:
                        print(f"Skipping set data as all values are None and no notes provided: {values}")
                        continue
                else:
                    print(f"Skipping set data due to unexpected format or missing 'values' key: {set_data_from_llm}")
                    continue
                
                if set_obj:
                    exercise_model.sets.append(set_obj)

            if exercise_model.sets:
                block_model.exercises.append(exercise_model)

        if block_model.exercises:
            workout_model.blocks.append(block_model)

    return workout_model
