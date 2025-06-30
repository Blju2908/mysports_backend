from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Optional
from pathlib import Path
from datetime import datetime

from app.models.workout_model import Workout
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.models.training_plan_model import TrainingPlan
from sqlmodel import select
from app.llm.workout_rationale.workout_rationale_chain import generate_workout_rationale_llm


async def get_user_id_from_workout_id(workout_id: int, db: AsyncSession) -> UUID | None:
    """
    ✅ SQLModel Best Practice: Direct query using db.scalar() one-liner.
    
    Args:
        workout_id: Die ID des Workouts
        db: Die Datenbankverbindung
        
    Returns:
        Die User-ID oder None, falls nicht gefunden
    """
    try:
        # ✅ SQLModel One-Liner
        return await db.scalar(
            select(Workout.user_id).where(Workout.id == workout_id)
        )
    except Exception as e:
        print(f"Error getting user_id from workout_id {workout_id}: {e}")
        return None


async def get_workout_with_details(workout_id: int, db: AsyncSession) -> Workout | None:
    """
    ✅ SQLModel Best Practice: Loads a workout with all details using eager loading.
    
    Args:
        workout_id: Die ID des Workouts
        db: Die Datenbankverbindung
        
    Returns:
        Das vollständige Workout-Objekt oder None
    """
    try:
        from sqlalchemy.orm import selectinload
        from app.models.block_model import Block
        from app.models.exercise_model import Exercise
        
        print(f"🔍 Loading workout {workout_id} with details...")
        
        # ✅ SQLModel One-Liner with eager loading
        workout = await db.scalar(
            select(Workout)
            .options(
                selectinload(Workout.blocks)
                .selectinload(Block.exercises)
                .selectinload(Exercise.sets)
            )
            .where(Workout.id == workout_id)
        )
        
        if workout:
            print(f"✅ Workout loaded successfully: {workout.name}")
        else:
            print(f"❌ Workout {workout_id} not found")
            
        return workout
        
    except Exception as e:
        print(f"❌ Error loading workout {workout_id}: {e}")
        import traceback
        traceback.print_exc()
        return None


def format_workout_for_llm(workout: Workout) -> str:
    """
    Formatiert ein Workout für die LLM-Verarbeitung.
    Enthält alle relevanten Details für die sportwissenschaftliche Analyse.
    
    Args:
        workout: Das Workout-Objekt
        
    Returns:
        Eine formatierte String-Darstellung des Workouts
    """
    if not workout:
        return "Kein Workout verfügbar."
    
    sections = []
    
    # Basis-Informationen
    basic_info = [f"Name: {workout.name}"]
    if workout.date_created:
        basic_info.append(f"Datum: {workout.date_created.strftime('%d.%m.%Y')}")
    if workout.duration:
        basic_info.append(f"Geplante Dauer: {workout.duration} Minuten")
    if workout.focus:
        basic_info.append(f"Fokus: {workout.focus}")
    if workout.notes:
        basic_info.append(f"Notizen: {workout.notes}")
    
    sections.append("## Workout-Details\n" + "\n".join(basic_info))
    
    # Status
    status_text = f"Status: {workout.status.value}"
    sections.append(f"## Status\n{status_text}")
    
    # Blocks und Exercises - Detaillierte Analyse
    if workout.blocks:
        blocks_info = []
        for i, block in enumerate(workout.get_sorted_blocks(), 1):
            block_details = [f"### Block {i}: {block.name}"]
            
            if block.description:
                block_details.append(f"Beschreibung: {block.description}")
            
            if block.exercises:
                block_details.append("**Übungen:**")
                for j, exercise in enumerate(block.exercises, 1):
                    exercise_info = f"{j}. {exercise.name}"
                    
                    # Detaillierte Sets-Analyse für wissenschaftliche Begründung
                    if exercise.sets:
                        completed_sets = [s for s in exercise.sets if s.status.value == "done"]
                        planned_sets = [s for s in exercise.sets if s.status.value in ["planned", "done"]]
                        
                        sets_info = f" (Geplant: {len(planned_sets)}, Ausgeführt: {len(completed_sets)})"
                        
                        # Detaillierte Set-Parameter für sportwissenschaftliche Analyse
                        if planned_sets:
                            set_details = []
                            for k, s in enumerate(planned_sets, 1):
                                set_detail = f"Set {k}: "
                                if s.weight and s.reps:
                                    set_detail += f"{s.weight}kg × {s.reps} Wdh"
                                elif s.reps:
                                    set_detail += f"{s.reps} Wdh"
                                elif s.time:
                                    set_detail += f"{s.time}s"
                                elif s.distance:
                                    set_detail += f"{s.distance}m"
                                
                                if s.rest_time:
                                    set_detail += f" (Pause: {s.rest_time}s)"
                                
                                # Status hinzufügen
                                set_detail += f" [{s.status.value}]"
                                set_details.append(set_detail)
                            
                            sets_info += f"\n      {chr(10).join(set_details)}"
                        
                        exercise_info += sets_info
                    
                    if exercise.notes:
                        exercise_info += f"\n      Notizen: {exercise.notes}"
                    
                    block_details.append(f"   {exercise_info}")
            
            if block.notes:
                block_details.append(f"Block-Notizen: {block.notes}")
            
            blocks_info.append("\n".join(block_details))
        
        sections.append("## Workout-Struktur\n" + "\n\n".join(blocks_info))
    
    if not sections:
        return "Keine Workout-Daten verfügbar."
    
    return "\n\n".join(sections)


def format_training_history_for_llm(training_history: list[Workout]) -> str:
    """
    Formatiert die Trainingshistorie für die LLM-Verarbeitung.
    Fokussiert auf Trainingsprogression und -muster für wissenschaftliche Analyse.
    
    Args:
        training_history: Liste der vergangenen Workouts (neueste zuerst)
        
    Returns:
        Eine formatierte String-Darstellung der Trainingshistorie
    """
    if not training_history:
        return "Keine Trainingshistorie verfügbar."
    
    history_sections = []
    
    for i, workout in enumerate(training_history, 1):
        workout_info = [
            f"### Workout {i}: {workout.name}",
            f"Datum: {workout.date_created.strftime('%d.%m.%Y')} ({(datetime.now().date() - workout.date_created.date()).days} Tage her)",
        ]
        
        if workout.focus:
            workout_info.append(f"Fokus: {workout.focus}")
        
        # Trainingsvolumen und -intensität für wissenschaftliche Analyse
        if workout.blocks:
            total_exercises = 0
            total_sets = 0
            exercise_summary = []
            
            for block in workout.blocks:
                for exercise in block.exercises:
                    completed_sets = [s for s in exercise.sets if s.status.value == "done"]
                    if completed_sets:
                        total_exercises += 1
                        total_sets += len(completed_sets)
                        
                        # Beispiel-Set für Intensitätsbewertung
                        example_set = completed_sets[0]
                        set_info = exercise.name
                        if example_set.weight and example_set.reps:
                            set_info += f" ({len(completed_sets)}×{example_set.reps}@{example_set.weight}kg)"
                        elif example_set.reps:
                            set_info += f" ({len(completed_sets)}×{example_set.reps})"
                        elif example_set.time:
                            set_info += f" ({len(completed_sets)}×{example_set.time}s)"
                        
                        exercise_summary.append(set_info)
            
            workout_info.append(f"Trainingsvolumen: {total_exercises} Übungen, {total_sets} Sets")
            if exercise_summary:
                workout_info.append(f"Hauptübungen: {', '.join(exercise_summary[:4])}")  # Top 4 für Übersicht
                if len(exercise_summary) > 4:
                    workout_info.append(f"... und {len(exercise_summary) - 4} weitere")
        
        if workout.notes:
            workout_info.append(f"Notizen: {workout.notes}")
        
        history_sections.append("\n".join(workout_info))
    
    return f"## Trainingshistorie (letzte {len(training_history)} Workouts)\n\n" + "\n\n".join(history_sections)


def format_training_plan_for_llm(training_plan) -> str:
    """
    Formatiert den Trainingsplan für die LLM-Verarbeitung.
    Gleiche Logik wie in workout_generation für Konsistenz.
    
    Args:
        training_plan: Das TrainingPlan-Objekt
        
    Returns:
        Eine formatierte String-Darstellung des Trainingsplans
    """
    if not training_plan:
        return "Kein Trainingsplan verfügbar."
    
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
    
    # Training Goals - Erweiterte Analyse
    goals_info = []
    if training_plan.workout_styles:
        goals_info.append(f"Bevorzugter Workout Style: {', '.join(training_plan.workout_styles)}")
    if training_plan.goal_details:
        goals_info.append(f"Ziel-Beschreibung: {training_plan.goal_details}")
    
    if goals_info:
        sections.append("## Trainingsziele\n" + "\n".join(goals_info))
    
    # Experience Level
    experience_info = []
    if training_plan.fitness_level is not None:
        fitness_labels = {
            1: "Sehr unfit", 2: "Unfit", 3: "Durchschnittlich", 
            4: "Fit", 5: "Sehr fit", 6: "Athletisch", 7: "Elite"
        }
        experience_info.append(f"Fitnesslevel: {fitness_labels.get(training_plan.fitness_level, training_plan.fitness_level)} ({training_plan.fitness_level}/7)")
    if training_plan.experience_level is not None:
        exp_labels = {
            1: "Anfänger", 2: "Wenig Erfahrung", 3: "Grundkenntnisse", 
            4: "Etwas Erfahrung", 5: "Erfahren", 6: "Sehr erfahren", 7: "Experte"
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
        schedule_info.append(f"Andere Aktivitäten: {training_plan.other_regular_activities}")
    
    if schedule_info:
        sections.append("## Trainingsplan\n" + "\n".join(schedule_info))
    
    # Equipment & Environment
    equipment_info = []
    if training_plan.equipment:
        equipment_info.append(f"Verfügbares Equipment: {', '.join(training_plan.equipment)}")
    if training_plan.equipment_details:
        equipment_info.append(f"Equipment-Details: {training_plan.equipment_details}")
    
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


async def run_workout_rationale_chain(
    user_id: UUID,
    workout_id: int,
    db: AsyncSession,
) -> str:
    """
    ✅ SQLModel Best Practice: Workout-Rationale-Generierung mit direkten Queries.
    
    Args:
        user_id: Die ID des Benutzers
        workout_id: Die ID des spezifischen Workouts
        db: Die Datenbankverbindung
        
    Returns:
        Eine sportwissenschaftliche Begründung als Text
    """
    # ✅ Load workout with details using optimized function
    workout = await get_workout_with_details(workout_id, db)
    if not workout:
        raise ValueError(f"Workout mit ID {workout_id} nicht gefunden")
    
    # ✅ SQLModel One-Liner: Direct TrainingPlan query
    training_plan = await db.scalar(
        select(TrainingPlan).where(TrainingPlan.user_id == user_id)
    )
    formatted_training_plan = format_training_plan_for_llm(training_plan) if training_plan else None
    
    # ✅ Load training history using optimized function
    try:
        training_history = await get_training_history_for_user_from_db(user_id, db, limit=5)
        formatted_history = format_training_history_for_llm(training_history)
    except Exception as e:
        print(f"⚠️ Could not load training history: {e}")
        formatted_history = "Trainingshistorie temporär nicht verfügbar."
    
    # Format current workout
    formatted_workout = format_workout_for_llm(workout)
    
    # LLM-Call für sportwissenschaftliche Begründung
    rationale_text = await generate_workout_rationale_llm(
        current_workout=formatted_workout,
        training_plan=formatted_training_plan,
        training_history=formatted_history,
        user_id=str(user_id),
        workout_id=workout_id
    )
    
    return rationale_text


async def generate_workout_rationale(
    user_id: UUID, 
    workout_id: int, 
    use_production_db: bool = False
) -> str:
    """
    Haupteinstiegspunkt für die Workout-Rationale-Generierung.
    
    Args:
        user_id: Die User-ID
        workout_id: Die Workout-ID
        use_production_db: Ob die Produktionsdatenbank verwendet werden soll
        
    Returns:
        Eine sportwissenschaftliche Begründung als Text
    """
    from app.llm.utils.db_utils import create_db_session
    
    async for db in create_db_session(use_production=use_production_db):
        return await run_workout_rationale_chain(user_id, workout_id, db)
        break  # Wichtig: break nach der Operation 