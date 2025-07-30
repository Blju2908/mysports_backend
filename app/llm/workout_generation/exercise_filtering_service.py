from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.exercise_description_model import ExerciseDescription


async def get_all_exercises_for_prompt(db_session: AsyncSession) -> str:
    """
    Loads all English exercise names from the database for the prompt, using a provided session.
    If no session is provided, it returns a minimal, hardcoded list.
    """
    try:
        # Lade nur die benötigten Spalten, nicht das komplette Model
        # Das umgeht das Problem mit der fehlenden 'aliases' Spalte
        stmt = select(
            ExerciseDescription.name_english,
            ExerciseDescription.is_unilateral
        ).order_by(ExerciseDescription.name_german)
        
        result = await db_session.execute(stmt)
        exercises = result.all()
        
        # Namen mit unilateral Tag extrahieren und formatieren
        formatted_names = []
        for name_english, is_unilateral in exercises:
            if name_english:
                name = name_english
                # Füge [unilateral] Tag hinzu wenn nötig
                if is_unilateral:
                    name = f"{name} [unilateral]"
                formatted_names.append(f"- {name}")
        
        formatted_names.sort()  # Alphabetisch sortieren
        
        return "# Available Exercises\n\n" + "\n".join(formatted_names)
            
    except Exception as e:
        print(f"❌ Error loading exercises from database: {e}")
        return "# Available Exercises\n\n- Push-up\n- Squat\n- Pull-up\n- Plank"