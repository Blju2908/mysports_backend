from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.exercise_description_model import ExerciseDescription


async def get_all_exercises_for_prompt(db_session: AsyncSession) -> str:
    """
    Loads all English exercise names from the database for the prompt, using a provided session.
    If no session is provided, it returns a minimal, hardcoded list.
    """
    try:
        # Load only the required columns to avoid issues with missing columns
        stmt = select(
            ExerciseDescription.name_english,
            ExerciseDescription.is_unilateral
        ).order_by(ExerciseDescription.name_german)
        
        result = await db_session.execute(stmt)
        exercises = result.all()
        
        # Extract names with unilateral tag and format
        formatted_names = []
        for name_english, is_unilateral in exercises:
            if name_english:
                name = name_english
                # Add [unilateral] tag if needed
                if is_unilateral:
                    name = f"{name} [unilateral]"
                formatted_names.append(f"- {name}")
        
        formatted_names.sort()  # Sort alphabetically
        
        return "# Available Exercises\n\n" + "\n".join(formatted_names)
            
    except Exception as e:
        print(f"❌ Error loading exercises from database: {e}")
        # Return a basic set of exercises as fallback
        return """# Available Exercises

- Air Squat
- Arm Circles
- Band Pull-Aparts
- Barbell Bench Press
- Barbell Bent Over Row
- Barbell Curl
- Barbell Deadlift
- Barbell Front Squat
- Bulgarian Split Squat [unilateral]
- Burpee
- Cat-Cow Flow
- Child's Pose
- Chin-up
- Deadlift
- Dumbbell Bench Press
- Dumbbell Curl
- Dumbbell Row [unilateral]
- Dynamic Walking Lunges [unilateral]
- Face Pull
- Farmer's Carry
- Goblet Squat
- Hammer Curl
- Jumping Jacks
- Kettlebell Swing
- Lateral Raise
- Mountain Climber
- Plank Hold
- Pull-up
- Push-up
- Romanian Deadlift
- Russian Twist
- Single-Arm Dumbbell Row [unilateral]
- Single-Arm Kettlebell Clean [unilateral]
- Squat
- Turkish Get-Up [unilateral]
- Wall Ball
"""