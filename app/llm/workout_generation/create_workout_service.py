from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Any, List, Dict, Optional, Literal
import json
from datetime import datetime

from app.models.training_plan_model import TrainingPlan
from sqlmodel import select
from sqlalchemy.orm import selectinload
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.workout_generation_chain import (
    execute_workout_generation_sequence,
)
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.models.workout_model import Workout
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set


# ✅ NEW: Atomic workout replacement following SQLModel best practices
async def replace_workout_atomically(
    db: AsyncSession,
    workout_id: int,
    user_id: UUID,
    new_workout_data: Dict[str, Any],
    training_plan_id: Optional[int] = None
) -> Workout:
    """
    ✅ SQLModel Best Practice: Atomare Workout-Ersetzung mit User-Validation
    
    Vorteile:
    - Vollständig atomare Transaktion (kein Datenverlust möglich)
    - User Authorization Check (Sicherheit)
    - UPDATE statt DELETE+INSERT (behält ID und Constraints bei)
    - Proper Error Handling mit automatischem Rollback
    - Cascade-Löschung für Beziehungen
    
    Args:
        db: Database session
        workout_id: ID des zu ersetzenden Workouts
        user_id: User ID für Authorization
        new_workout_data: Neue Workout-Daten (von LLM)
        training_plan_id: Optional training plan ID
        
    Returns:
        Das aktualisierte Workout-Objekt
        
    Raises:
        ValueError: Wenn Workout nicht gefunden
        PermissionError: Wenn User nicht berechtigt
    """
    # ✅ Nutze die bestehende Session-Transaktion (keine zusätzliche db.begin() nötig)
    # 1. Lade und validiere existing workout mit EAGER LOADING (verhindert lazy loading)
    stmt = select(Workout).options(
        selectinload(Workout.blocks)
        .selectinload(Block.exercises)
        .selectinload(Exercise.sets)
    ).where(Workout.id == workout_id)
    
    result = await db.execute(stmt)
    existing_workout = result.scalar_one_or_none()
    
    if not existing_workout:
        raise ValueError(f"Workout mit ID {workout_id} nicht gefunden.")
    
    # 3. ✅ UPDATE Workout-Hauptdaten (behält ID bei)
    existing_workout.name = clean_text_data(new_workout_data.get("name", "Unbenanntes Workout"))
    existing_workout.description = clean_text_data(new_workout_data.get("description"))
    existing_workout.focus = clean_text_data(new_workout_data.get("focus"))
    existing_workout.duration = new_workout_data.get("duration")
    existing_workout.date_created = datetime.utcnow()  # Update timestamp
    existing_workout.training_plan_id = training_plan_id  # Update training plan reference
    
    # 4. ✅ Lösche alte Beziehungen (CASCADE löscht automatisch Sets und Exercises)
    for block in existing_workout.blocks:
        await db.delete(block)
    await db.flush()  # Stelle sicher, dass alte Blöcke gelöscht sind
    
    # 5. ✅ Erstelle neue Beziehungen
    existing_workout.blocks = []
    for block_index, block_data in enumerate(new_workout_data.get("blocks", [])):
        block_model = Block(
            name=clean_text_data(block_data.get("name", "Unbenannter Block")),
            description=clean_text_data(block_data.get("description")),
            position=block_data.get("position", block_index),
            exercises=[],
        )

        for exercise_index, exercise_data in enumerate(block_data.get("exercises", [])):
            exercise_model = Exercise(
                name=clean_text_data(exercise_data.get("name", "Unbenannte Übung")),
                superset_id=clean_text_data(exercise_data.get("superset_id")),
                position=exercise_data.get("position", exercise_index),
                sets=[],
            )

            for set_index, set_data_from_llm in enumerate(exercise_data.get("sets", [])):
                if isinstance(set_data_from_llm, dict) and "values" in set_data_from_llm:
                    values = set_data_from_llm.get("values", [])
                    set_obj = Set.from_values_list(values)
                    
                    if set_obj:
                        set_obj.position = set_data_from_llm.get("position", set_index)
                        exercise_model.sets.append(set_obj)

            if exercise_model.sets:
                block_model.exercises.append(exercise_model)

        if block_model.exercises:
            existing_workout.blocks.append(block_model)
    
    # 6. ✅ Commit erfolgt automatisch durch create_background_session()
    await db.commit()
    await db.refresh(existing_workout)
    return existing_workout


async def save_workout_schema_to_db(
    db: AsyncSession,
    workout_schema: WorkoutSchema,
    user_id: UUID,
    training_plan_id: Optional[int] = None,
    workout_id: Optional[int] = None
) -> Workout:
    """
    ✅ NEW: Saves or updates a workout schema to the database efficiently
    
    Args:
        db: Database session
        workout_schema: Generated workout schema from LLM
        user_id: User ID for ownership
        training_plan_id: Optional training plan ID
        workout_id: Optional - if provided, updates existing workout
    
    Returns:
        The saved/updated workout object
    """
    workout_dict = workout_schema.model_dump()
    
    if workout_id:
        # Update existing workout
        return await replace_workout_atomically(
            db=db,
            workout_id=workout_id,
            user_id=user_id,
            new_workout_data=workout_dict,
            training_plan_id=training_plan_id
        )
    else:
        # Create new workout
        workout_model = convert_llm_output_to_db_models(
            workout_dict=workout_dict,
            user_id=user_id,
            training_plan_id=training_plan_id,
        )
        
        db.add(workout_model)
        await db.commit()
        await db.refresh(workout_model)
        return workout_model


async def run_workout_chain(
    user_id: UUID | None,
    user_prompt: str | None,
    db: AsyncSession,
    save_to_db: bool = True,
    use_exercise_filtering: bool = False,
    workout_id: Optional[int] = None
) -> Any:
    """
    ✅ ENHANCED: Führt den Workout-Generierungs-Prozess mit dem LLM durch.
    Kann optional Exercise Filtering verwenden und bestehende Workouts aktualisieren.

    Args:
        user_id: Die ID des Benutzers.
        user_prompt: Ein optionaler Prompt des Benutzers.
        db: Die Datenbankverbindung.
        save_to_db: Wenn True, wird das Workout in der DB gespeichert.
        use_exercise_filtering: Wenn True, werden Übungen aus der DB gefiltert.
        workout_id: Optional - wenn angegeben, wird das bestehende Workout aktualisiert.
    """

    formatted_training_plan = None
    training_plan_db_obj = None
    training_plan_id_for_saving = None
    formatted_history = None

    if user_id is not None:
        # Lade TrainingPlan-Objekt (wird für Filterung und Formatierung benötigt)
        training_plan_db_obj = await db.scalar(
            select(TrainingPlan).where(TrainingPlan.user_id == user_id)
        )
        if training_plan_db_obj:
            training_plan_id_for_saving = training_plan_db_obj.id
            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

        # Lade Trainingshistorie
        raw_training_history: List[Workout] = (
            await get_training_history_for_user_from_db(user_id, db, limit=10)
        )
        if raw_training_history:
            formatted_history = format_training_history_for_llm(raw_training_history)
    
    # LLM-Call durchführen mit der neuen, vereinheitlichten Funktion
    workout_schema = await execute_workout_generation_sequence(
        training_plan_obj=training_plan_db_obj,
        training_plan_str=formatted_training_plan,
        training_history=formatted_history,
        user_prompt=user_prompt,
        db=db,
        use_exercise_filtering=use_exercise_filtering,

    )

    # Speichern des Workouts in der DB
    if save_to_db:
        if not user_id:
            raise ValueError("user_id ist erforderlich, um das Workout zu speichern.")
        
        if workout_id:
            # ✅ IMPROVED: Atomare Workout-Ersetzung mit User-Validation
            try:
                updated_workout = await replace_workout_atomically(
                    db=db,
                    workout_id=workout_id,
                    user_id=user_id,
                    new_workout_data=workout_schema.model_dump(),
                    training_plan_id=training_plan_id_for_saving
                )
                print(f"✅ Workout atomisch aktualisiert mit ID: {updated_workout.id}")
                return updated_workout
            except PermissionError as pe:
                raise ValueError(f"Berechtigung verweigert: {str(pe)}")
            except Exception as e:
                print(f"❌ Fehler bei atomarer Workout-Ersetzung: {str(e)}")
                raise
        else:
            # ✅ CREATE: Neues Workout erstellen
            workout_model = convert_llm_output_to_db_models(
                workout_schema.model_dump(),
                user_id=user_id,
                training_plan_id=training_plan_id_for_saving,
            )
            
            db.add(workout_model)
            await db.commit()
            await db.refresh(workout_model)
            print(f"✅ Workout erfolgreich in Datenbank gespeichert mit ID: {workout_model.id}")
            return workout_model
    else:
        # Rückgabe des strukturierten Schemas
        return workout_schema

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

def clean_text_data(text: str | None) -> str | None:
    """
    Entfernt problematische Zeichen wie Null-Bytes aus Textdaten.
    """
    if text is None:
        return None
    
    # Entferne Null-Bytes und andere problematische Zeichen
    cleaned = text.replace('\x00', '').replace('\r', '').strip()
    return cleaned if cleaned else None

def convert_llm_output_to_db_models(
    workout_dict: Dict[str, Any],  
    user_id: UUID,  
    training_plan_id: Optional[int] = None,
) -> Workout:
    """
    ✅ OPTIMIZED: Konvertiert das LLM-Output in ein Workout-DB-Modell mit direkter User-Beziehung.
    Nutzt die neue user_id als primäre Beziehung und behält training_plan_id für Kontext.
    Die 'values' Liste in SetSchema wird in die entsprechenden Felder des Set-Modells gemappt.
    [weight, reps, duration, distance, rest_time]

    Args:
        workout_dict: Das LLM-Output als Dict (von WorkoutSchema.model_dump()).
        user_id: Die User-ID für direkte Beziehung (REQUIRED).
        training_plan_id: Optional die ID des Trainingsplans (für Kontext).

    Returns:
        Ein Workout-Modell mit allen Beziehungen.
    """
    # ✅ IMPROVED: Erstelle das Workout-Modell mit direkter user_id Beziehung
    workout_model = Workout(
        user_id=user_id,  # ✅ NEW: Direct user relationship!
        training_plan_id=training_plan_id,  # Keep for context
        name=clean_text_data(workout_dict.get("name", "Unbenanntes Workout")),
        description=clean_text_data(workout_dict.get("description")),
        focus=clean_text_data(workout_dict.get("focus")),
        duration=workout_dict.get("duration"),
        date_created=datetime.utcnow(),
        blocks=[],
    )

    for block_index, block_data in enumerate(workout_dict.get("blocks", [])):
        block_model = Block(
            name=clean_text_data(block_data.get("name", "Unbenannter Block")),
            description=clean_text_data(block_data.get("description")),
            position=block_data.get("position", block_index),  # Use LLM position or fallback to index
            exercises=[],
        )

        for exercise_index, exercise_data in enumerate(block_data.get("exercises", [])):
            exercise_model = Exercise(
                name=clean_text_data(exercise_data.get("name", "Unbenannte Übung")),
                superset_id=clean_text_data(exercise_data.get("superset_id")),
                position=exercise_data.get("position", exercise_index),  # Use LLM position or fallback to index
                sets=[],
            )

            for set_index, set_data_from_llm in enumerate(exercise_data.get("sets", [])):
                # ✅ OPTIMIZED: Verwende die bewährte Set.from_values_list Methode
                if isinstance(set_data_from_llm, dict) and "values" in set_data_from_llm:
                    values = set_data_from_llm.get("values", [])
                    set_obj = Set.from_values_list(values)
                    
                    if set_obj:
                        # Add position to the set
                        set_obj.position = set_data_from_llm.get("position", set_index)
                        exercise_model.sets.append(set_obj)
                    else:
                        print(f"⚠️ Skipping set data - no valid values: {values}")
                else:
                    print(f"⚠️ Skipping set data due to unexpected format or missing 'values' key: {set_data_from_llm}")

            if exercise_model.sets:
                block_model.exercises.append(exercise_model)

        if block_model.exercises:
            workout_model.blocks.append(block_model)

    return workout_model
