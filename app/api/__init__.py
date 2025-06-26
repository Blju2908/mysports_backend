from fastapi import APIRouter

from .llm_endpoint import router as llm_router
from .auth_endpoint import router as auth_router
from .training_plan_endpoint import router as training_plan_router
from .workout_endpoint import router as workout_router
from .feedback_endpoint import router as feedback_router
from .showcase_endpoint import router as showcase_router
from .llm_log_endpoint import router as llm_log_router
from .frontend.landing_page_survey_endpoint import router as landing_survey_router

# ✅ NEW: Import V1 API Router
from .v1 import create_api_v1_router

def create_api_router() -> APIRouter:
    """
    Create main API router with both original and V1 endpoints
    - Original endpoints: for Live App compatibility (no URL changes)
    - V1 endpoints: enhanced version with position support
    """
    api_router = APIRouter()
    
    # ✅ ORIGINAL ENDPOINTS - Live App compatibility (NO URL CHANGES!)
    api_router.include_router(llm_router, tags=["llm"])
    api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    api_router.include_router(training_plan_router, prefix="/training-plan", tags=["training-plan"])
    api_router.include_router(workout_router, prefix="/workouts", tags=["workout"])
    api_router.include_router(feedback_router, prefix="/feedback", tags=["feedback"])
    api_router.include_router(showcase_router, tags=["showcase"])
    api_router.include_router(llm_log_router, tags=["llm-logs"])
    api_router.include_router(landing_survey_router, prefix="/frontend", tags=["frontend"])
    
    # ✅ NEW V1 ENDPOINTS - Enhanced version with position support
    v1_router = create_api_v1_router()
    api_router.include_router(v1_router, prefix="/v1")
    
    return api_router 