from uuid import UUID
from sqlmodel import select

from app.db.session import get_background_session
from app.services.workout_service import get_exercises_with_done_sets_only
from app.schemas.workout_schema import ExerciseRead
from app.schemas.exercise_description_schema import ExerciseDescriptionRead
from app.models.exercise_description_model import ExerciseDescription 

async def create_workout_main_flow(user_id: UUID, session_duration: int, profile_id: int):

    training_history_dtos, exercise_descriptions_dtos = await load_workout_creation_data(user_id)

    print(training_history_dtos)
    print(exercise_descriptions_dtos)
    print("Ende")




async def load_workout_creation_data(user_id: UUID):
    async with get_background_session() as db_session:
        
        # Load Training History
        training_history_db = await get_exercises_with_done_sets_only(db_session, user_id, number_of_workouts=10)
        training_history_dtos = [ExerciseRead.model_validate(exercise) for exercise in training_history_db]

        # Load Exercise Descriptions
        exercise_descriptions_db = await db_session.execute(select(ExerciseDescription))
        exercise_descriptions = exercise_descriptions_db.scalars().all()
        exercise_descriptions_dtos = [ExerciseDescriptionRead.model_validate(exercise_description) for exercise_description in exercise_descriptions]

    return training_history_dtos, exercise_descriptions_dtos