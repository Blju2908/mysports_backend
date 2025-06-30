from fastapi import APIRouter

# ✅ NEW: Import V1 API Router
from .v1 import create_api_v1_router

def create_api_router() -> APIRouter:
    """
    Create main API router with both original and V1 endpoints
    - Original endpoints: for Live App compatibility (no URL changes)
    - V1 endpoints: enhanced version with position support
    """
    api_router = APIRouter()
    
    # ✅ NEW V1 ENDPOINTS - Enhanced version with position support
    v1_router = create_api_v1_router()
    api_router.include_router(v1_router, prefix="/v1")
    
    return api_router 