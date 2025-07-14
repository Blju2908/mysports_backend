from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.exercise_description_db_access import get_all_exercise_names


async def get_all_exercises_for_prompt(db_session: AsyncSession) -> str:
    """
    Loads all English exercise names from the database for the prompt, using a provided session.
    If no session is provided, it returns a minimal, hardcoded list.
    """
    try:
        # Lade alle Übungen aus DB
        all_exercises = await get_all_exercise_names(db_session)
        
        # Namen mit unilateral Tag extrahieren und formatieren
        formatted_names = []
        for ex in all_exercises:
            if ex.name_english:
                name = ex.name_english
                # Füge [unilateral] Tag hinzu wenn nötig
                if ex.is_unilateral:
                    name = f"{name} [unilateral]"
                formatted_names.append(f"- {name}")
        
        formatted_names.sort()  # Alphabetisch sortieren
        
        return "# Available Exercises\n\n" + "\n".join(formatted_names)
            
    except Exception as e:
        print(f"❌ Error loading exercises from database: {e}")
        return "# Available Exercises\n\n- Push-up\n- Squat"