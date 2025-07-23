from fastapi import APIRouter

from .llm_endpoint import router as llm_router
from .auth_endpoint import router as auth_router
from .training_plan_endpoint import router as training_plan_router
from .workout_endpoint import router as workout_router
from .feedback_endpoint import router as feedback_router
from .showcase_endpoint import router as showcase_router
from .llm_log_endpoint import router as llm_log_router
from .training_profile_endpoint import router as training_profile_router

def create_api_v2_router() -> APIRouter:
    """
    Create API Router
    Enhanced version with position support for stable sorting
    """
    api_router = APIRouter()
    
    # V1 Endpoints - Hierarchical tags with V1 prefix for better docs structure
    api_router.include_router(llm_router, tags=["LLM"])
    api_router.include_router(auth_router, prefix="/auth", tags=["Authentication"])
    api_router.include_router(training_plan_router, prefix="/training-plan", tags=["Training Plans"])
    api_router.include_router(workout_router, prefix="/workouts", tags=["Workouts"])
    api_router.include_router(feedback_router, prefix="/feedback", tags=["Feedback"])
    api_router.include_router(showcase_router, tags=["Showcase"])
    api_router.include_router(llm_log_router, tags=["LLM Logs"])
    api_router.include_router(training_profile_router, prefix="/training-profiles", tags=["Training Profiles"])
    
    return api_router 