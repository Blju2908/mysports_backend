from typing import List
import json

from pydantic.types import T
from app.models.workout_model import Workout
from app.models.training_plan_model import TrainingPlan, TrainingProfile

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

def format_training_plan_for_llm_v2(training_plan: TrainingPlan, profile: TrainingProfile) -> str:
    """
    Formats the training plan data into a structured text format for the LLM.
    Converts all training plan attributes into readable sections.
    """
    sections = []
    
    # Personal Information
    personal_info = []
    if training_plan.gender:
        personal_info.append(f"Geschlecht: {training_plan.gender}")
    if training_plan.age:
        personal_info.append(f"Alter: {training_plan.age} Jahre")
    if training_plan.height:
        personal_info.append(f"Körpergröße: {training_plan.height} cm")
    if training_plan.weight:
        personal_info.append(f"Gewicht: {training_plan.weight} kg")
    
    if personal_info:
        sections.append("## Persönliche Informationen\n" + "\n".join(personal_info))
    
    # Training Goals
    goals_info = []
    if training_plan.workout_goal_llm_context:
        goals_info.append(f"Bevorzugter Workout Style: {training_plan.workout_goal_llm_context}")
    if training_plan.goal_details:
        goals_info.append(f"Detaillierte Zielbeschreibung: {training_plan.goal_details}")
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
        experience_info.append(f"Fitnesslevel: {fitness_labels.get(training_plan.fitness_level)} ({training_plan.fitness_level}/7)")
    if training_plan.fitness_level_description:
        experience_info.append(f"Fitnesslevel Beschreibung: {training_plan.fitness_level_description}")

    if training_plan.experience_level is not None:
        exp_labels = {
            1: "Anfänger", 
            2: "Fortgeschritten", 
            3: "Experte",
        }
        experience_info.append(f"Trainingserfahrung: {exp_labels.get(training_plan.experience_level)} ({training_plan.experience_level}/3)")
    if training_plan.experience_level_description:
        experience_info.append(f"Trainingserfahrung Beschreibung: {training_plan.experience_level_description}")
    
    if experience_info:
        sections.append("## Erfahrungslevel\n" + "\n".join(experience_info))
    
    # Training Schedule
    schedule_info = []
    if training_plan.training_frequency:
        schedule_info.append(f"Trainingsfrequenz: {training_plan.training_frequency}x pro Woche")
    if training_plan.session_duration:
        schedule_info.append(f"Trainingsdauer: {training_plan.session_duration} Minuten")
    if schedule_info:
        sections.append("## Trainingsplan\n" + "\n".join(schedule_info))
    
    # Equipment & Environment
    equipment_info = []
    if profile.equipment:
        # Directly use equipment values from database without separate mapping logic
        equipment_info.append(f"Standard Ausrüstung: {', '.join(profile.equipment)}")
    if profile.equipment_llm_context:
        equipment_info.append(f"Zusätzliche Informationen: {profile.equipment_llm_context}")
    if profile.equipment_details:
        equipment_info.append(f"Zusätzliche Informationen: {profile.equipment_details}")
    if equipment_info:
        sections.append("## Equipment & Umgebung\n" + "\n".join(equipment_info))
    
    # Restrictions
    restrictions_info = []
    if training_plan.restrictions:
        restrictions_info.append(f"Verletzungen/Einschränkungen: {training_plan.restrictions}")
    
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