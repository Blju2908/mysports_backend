from typing import List, Optional
from sqlmodel.ext.asyncio.session import AsyncSession
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field
from app.core.config import get_config
from app.models.exercise_description_model import ExerciseDescription
from app.models.training_plan_model import TrainingPlan
from app.db.exercise_description_db_access import get_equipment_list, filter_exercises_advanced, get_all_exercise_names


class EquipmentMatchingResponse(BaseModel):
    """Response Schema für Equipment Matching"""
    available_equipment: List[str] = Field(description="Equipment das dem User zur Verfügung steht")


async def get_filtered_exercises_for_user(
    training_plan: TrainingPlan,
    db: AsyncSession,
    user_prompt: Optional[str] = None
) -> Optional[str]:
    """
    Filtert Übungen basierend auf User Equipment und Experience Level.
    Returns None if filtering should be skipped.
    """
    try:
        from datetime import datetime
        _start_filtering = datetime.now()
        # 1. Difficulty Level Logic
        allowed_difficulties = get_difficulty_levels_for_experience(training_plan.experience_level)
        
        # 2. Equipment Matching via LLM
        available_equipment = []
        if training_plan.equipment:
            _start_equipment_matching = datetime.now()
            all_db_equipment = await get_equipment_list(db)
            available_equipment = await match_user_equipment_with_llm(
                user_default_environment=training_plan.equipment,
                user_equipment_details=training_plan.equipment_details,
                all_db_equipment=all_db_equipment,
                user_prompt=user_prompt
            )
            _equipment_duration = (datetime.now() - _start_equipment_matching).total_seconds()
            print(f"⏱️ equipment_matching LLM duration: {_equipment_duration:.1f}s")
        
        # 3. Filter exercises from DB
        filtered_exercises = await filter_exercises_advanced(
            db=db,
            equipment=available_equipment if available_equipment else None,
            difficulty_levels=allowed_difficulties,
        )
        
        if not filtered_exercises:
            print("⚠️ No exercises found with current filters, will use default prompt exercises")
            return None
        
        # 4. ✅ EXTRACT DATA IMMEDIATELY while session is active to prevent detached object issues
        exercise_data = []
        for ex in filtered_exercises:
            exercise_data.append({
                'name_german': ex.name_german,
                'difficulty_level': ex.difficulty_level,
                'equipment_options': ex.equipment_options or []
            })
        
        # 5. Format exercises using extracted data (no more DB object dependencies)
        formatted_exercises = format_exercise_data_for_prompt(exercise_data)
        
        _filtering_duration = (datetime.now() - _start_filtering).total_seconds()
        print(f"⏱️ exercise_filtering total duration: {_filtering_duration:.1f}s")
        print(f"🎯 Exercise Filtering Results:")
        print(f"   Equipment: {len(available_equipment)} options")
        print(f"   Difficulty: {allowed_difficulties}")
        print(f"   Filtered exercises: {len(filtered_exercises)}")
        
        return formatted_exercises
        
    except Exception as e:
        print(f"❌ Error in exercise filtering: {e}")
        return None


def get_difficulty_levels_for_experience(experience_level: Optional[int]) -> List[str]:
    """Bestimmt Difficulty Levels basierend auf experience_level"""
    if experience_level is None or experience_level < 3:
        return ["Anfänger"]
    elif experience_level <= 6:
        return ["Anfänger", "Fortgeschritten"]
    else:
        return ["Anfänger", "Fortgeschritten", "Experte"]


async def match_user_equipment_with_llm(
    user_default_environment: List[str],
    user_equipment_details: List[str],
    all_db_equipment: List[str],
    user_prompt: Optional[str] = None
) -> List[str]:
    """Matcht User Equipment mit DB Equipment via LLM"""
    
    # Lade Prompt aus Datei (gleiche Pattern wie workout_generation_chain.py)
    from pathlib import Path
    prompt_path = Path(__file__).parent / "prompts" / "equipment_matching_prompt.md"
    with open(prompt_path, 'r', encoding='utf-8') as f:
        prompt_template_content = f.read()
    
    # Format prompt mit Variablen (gleiche Pattern wie workout_generation_chain.py)
    formatted_prompt = prompt_template_content.format(
        user_default_environment=', '.join(user_default_environment),
        user_equipment_details=', '.join(user_equipment_details),
        all_db_equipment=', '.join(all_db_equipment),
        user_prompt=user_prompt
    )
    
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=get_config().GOOGLE_API_KEY)
    structured_llm = llm.with_structured_output(EquipmentMatchingResponse)
    response = await structured_llm.ainvoke(formatted_prompt)
    
    # Validiere gegen DB Equipment
    valid_equipment = [eq for eq in response.available_equipment if eq in all_db_equipment]
    return valid_equipment


def format_exercise_data_for_prompt(exercise_data: List[dict]) -> str:
    """Formatiert Übungsdaten für Prompt (session-unabhängig)"""
    if not exercise_data:
        return ""
    
    formatted = []
    for data in exercise_data:
        name = data.get('name_german', 'Unknown Exercise')
        difficulty = data.get('difficulty_level', 'Anfänger')
        equipment = data.get('equipment_options', [])
        equipment_str = ', '.join(equipment) if equipment else 'Eigengewicht'
        
        formatted.append(f"- {name} ({difficulty}, {equipment_str})")
    
    return "\n".join(formatted)


def format_exercises_for_prompt(exercises: List[ExerciseDescription]) -> str:
    """Formatiert gefilterte Übungen für Prompt (DEPRECATED - use format_exercise_data_for_prompt)"""
    if not exercises:
        return ""
    
    formatted = []
    for ex in exercises:
        # ✅ Defensive Programmierung: Handle potential None values and detached objects
        try:
            name = getattr(ex, 'name_german', 'Unknown Exercise')
            difficulty = getattr(ex, 'difficulty_level', 'Unknown')
            # Equipment options could be None or empty list
            equipment = getattr(ex, 'equipment_options', [])
            equipment_str = ', '.join(equipment) if equipment else 'Eigengewicht'
            
            formatted.append(f"- {name} ({difficulty}, {equipment_str})")
        except Exception as e:
            print(f"⚠️ Error formatting exercise {getattr(ex, 'name_german', 'Unknown')}: {e}")
            # Fallback formatting
            formatted.append(f"- {getattr(ex, 'name_german', 'Unknown Exercise')} (Anfänger, Eigengewicht)")
    
    return "\n".join(formatted) 


async def get_all_exercises_for_prompt(db: [AsyncSession] = None) -> str:
    """
    Lädt alle deutschen Übungsnamen aus der Datenbank für den Prompt.
    Einfach und direkt - nur die Namen.
    """
    
    try:
        # Lade alle Übungen aus DB
        all_exercises = await get_all_exercise_names(db)
        
        # Nur die deutschen Namen extrahieren und formatieren
        exercise_names = [ex.name_german for ex in all_exercises if ex.name_german]
        exercise_names.sort()  # Alphabetisch sortieren
        
        # Einfache Formatierung für Prompt
        formatted_names = [f"- {name}" for name in exercise_names]
        
        return "# Verfügbare Übungen\n\n" + "\n".join(formatted_names)
        
    except Exception as e:
        print(f"❌ Error loading exercises from database: {e}")
        return "# Verfügbare Übungen\n\n- Push-up\n- Squat"