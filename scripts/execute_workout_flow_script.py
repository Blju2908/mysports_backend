# backend/scripts/execute_workout_flow.py
from uuid import UUID
from app.services.muscle_recorvery_model import MuscleRecoveryModel
from app.db.session import get_background_session
from app.services.workout_service import get_exercises_with_done_sets_only
from app.schemas.workout_schema import ExerciseRead
from app.schemas.exercise_description_schema import ExerciseDescriptionRead
from app.models.exercise_description_model import ExerciseDescription
from app.llm.utils.db_utils import create_db_session
from sqlmodel import select

from app.services.create_workout_service import create_workout_main_flow


async def execute_workout_flow():
    # Hier stehen quasi die Informationen, die sonst vom Endpoint kommen
    user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff")
    session_duration = 60
    profile_id = 33956

    await create_workout_main_flow(
        user_id=user_id, 
        session_duration=session_duration, 
        profile_id=profile_id
    )
