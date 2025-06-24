from fastapi import APIRouter

from .llm_endpoint import router as llm_router
from .auth_endpoint import router as auth_router
from .training_plan_endpoint import router as training_plan_router
from .workout_endpoint import router as workout_router
from .showcase_endpoint import router as showcase_router
from .llm_log_endpoint import router as llm_log_router
from .frontend.landing_page_survey_endpoint import router as landing_survey_router

def create_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(llm_router, tags=["llm"])
    api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    api_router.include_router(training_plan_router, prefix="/training-plan", tags=["training-plan"])
    api_router.include_router(workout_router, prefix="/workouts", tags=["workout"])
    api_router.include_router(showcase_router, tags=["showcase"])
    api_router.include_router(llm_log_router, tags=["llm-logs"])
    api_router.include_router(landing_survey_router, prefix="/frontend", tags=["frontend"])
    
    return api_router 