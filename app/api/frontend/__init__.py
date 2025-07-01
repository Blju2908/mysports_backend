from fastapi import APIRouter

from .landing_page_survey_endpoint import router as landing_survey_router

def create_frontend_router() -> APIRouter:
    """
    Create Frontend API Router
    """
    frontend_router = APIRouter()
    
    # Frontend endpoints
    frontend_router.include_router(landing_survey_router, tags=["Frontend"])
    
    return frontend_router 