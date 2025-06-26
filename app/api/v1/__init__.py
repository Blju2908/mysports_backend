from fastapi import APIRouter

from .llm_endpoint import router as llm_router
from .auth_endpoint import router as auth_router
from .training_plan_endpoint import router as training_plan_router
from .workout_endpoint import router as workout_router
from .feedback_endpoint import router as feedback_router
from .showcase_endpoint import router as showcase_router
from .llm_log_endpoint import router as llm_log_router
from .frontend.landing_page_survey_endpoint import router as landing_survey_router

def create_api_v1_router() -> APIRouter:
    """
    Create API V1 Router
    Enhanced version with position support for stable sorting
    """
    api_v1_router = APIRouter()
    
    # V1 Endpoints - Hierarchical tags with V1 prefix for better docs structure
    api_v1_router.include_router(llm_router, tags=["V1 - LLM"])
    api_v1_router.include_router(auth_router, prefix="/auth", tags=["V1 - Authentication"])
    api_v1_router.include_router(training_plan_router, prefix="/training-plan", tags=["V1 - Training Plans"])
    api_v1_router.include_router(workout_router, prefix="/workouts", tags=["V1 - Workouts"])
    api_v1_router.include_router(feedback_router, prefix="/feedback", tags=["V1 - Feedback"])
    api_v1_router.include_router(showcase_router, tags=["V1 - Showcase"])
    api_v1_router.include_router(llm_log_router, tags=["V1 - LLM Logs"])
    api_v1_router.include_router(landing_survey_router, prefix="/frontend", tags=["V1 - Frontend"])
    
    return api_v1_router 