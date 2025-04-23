from fastapi import APIRouter
from .user import router as user_router
from .llm_endpoint import router as llm_router
from .auth_endpoint import router as auth_router

def create_api_router() -> APIRouter:
    api_router = APIRouter()
    api_router.include_router(user_router, prefix="/users", tags=["users"])
    api_router.include_router(llm_router, tags=["llm"])
    api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
    return api_router 