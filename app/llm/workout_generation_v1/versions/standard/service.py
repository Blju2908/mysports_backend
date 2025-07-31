from typing import List
import json

from pydantic.types import T
from app.models.workout_model import Workout
from app.models.training_plan_model import TrainingPlan, TrainingProfile
from ...shared.formatting.training_plan import format_training_plan_for_llm, format_training_plan_for_llm_v2
from ...shared.formatting.training_history import format_training_history_for_llm

# Removed duplicate functions - now importing from shared/formatting/