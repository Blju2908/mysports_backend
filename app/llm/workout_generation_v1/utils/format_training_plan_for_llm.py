from app.models.training_plan_model import TrainingPlan
from app.models.training_plan_model import TrainingProfile


def format_training_plan_for_llm(training_plan: TrainingPlan, profile: TrainingProfile) -> str:
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