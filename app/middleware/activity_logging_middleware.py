import time
import json
from typing import Callable, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.activity_logger import activity_logger
from app.models.user_activity_log_model import ActivityActionType
from app.core.auth import get_current_user_optional
import logging

logger = logging.getLogger(__name__)

class ActivityLoggingMiddleware(BaseHTTPMiddleware):
    """
    Vereinfachte Middleware für User Activity Logging.
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/openapi.json", "/redoc", "/favicon.ico",
            "/health", "/metrics"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        start_time = time.time()
        
        # Parse request body if JSON
        request_data = None
        try:
            if request.headers.get("content-type", "").startswith("application/json"):
                body = await request.body()
                if body:
                    request_data = json.loads(body.decode())
                    request._body = body
        except Exception as e:
            logger.warning(f"Could not parse request body: {e}")
        
        # Get user if authenticated
        user = None
        try:
            user = await get_current_user_optional(request)
        except Exception:
            pass
        
        # Process request
        response = None
        error_message = None
        
        try:
            response = await call_next(request)
        except Exception as e:
            error_message = str(e)
            logger.error(f"Request failed: {e}")
            response = JSONResponse(
                status_code=500,
                content={"detail": "Internal server error"}
            )
        
        # Determine action type and extract resource info
        action_type = self.determine_action_type(request, response)
        resource_id, resource_type = self.extract_resource_info(request, response)
        
        # Log activity (always enabled for simplicity)
        try:
            await activity_logger.log_activity(
                request=request,
                response=response,
                action_type=action_type,
                user=user,
                resource_id=resource_id,
                resource_type=resource_type,
                request_data=request_data,
                error_message=error_message,
                start_time=start_time,
                analytics_enabled=True  # Simplifikation: Immer aktiviert
            )
        except Exception as e:
            logger.error(f"Failed to log activity: {e}")
        
        return response
    
    def determine_action_type(self, request: Request, response: Response) -> ActivityActionType:
        """
        Bestimmt den Action Type basierend auf Endpoint und HTTP Method.
        """
        path = request.url.path.lower()
        method = request.method.upper()
        
        # Authentication Endpoints
        if "/auth/" in path:
            if "login" in path:
                return ActivityActionType.LOGIN_SUCCESS if response.status_code < 400 else ActivityActionType.LOGIN_FAILED
            elif "logout" in path:
                return ActivityActionType.LOGOUT
            elif "register" in path:
                return ActivityActionType.REGISTER_SUCCESS if response.status_code < 400 else ActivityActionType.REGISTER_FAILED
            elif "request-otp" in path:
                return ActivityActionType.OTP_REQUEST
            elif "verify-otp" in path:
                return ActivityActionType.OTP_VERIFY_SUCCESS if response.status_code < 400 else ActivityActionType.OTP_VERIFY_FAILED
            elif "set-password" in path:
                return ActivityActionType.PASSWORD_CHANGE
            elif "change-email" in path:
                return ActivityActionType.EMAIL_CHANGE
            elif "refresh" in path:
                return ActivityActionType.TOKEN_REFRESH
        
        # Workout Endpoints
        elif "/workouts" in path:
            if method == "POST":
                return ActivityActionType.WORKOUT_CREATE
            elif method == "PUT" or method == "PATCH":
                return ActivityActionType.WORKOUT_UPDATE
            elif method == "DELETE":
                return ActivityActionType.WORKOUT_DELETE
            elif method == "GET":
                return ActivityActionType.WORKOUT_VIEW
        
        # Training Plan Endpoints
        elif "/training-plan" in path:
            if method == "POST":
                return ActivityActionType.TRAINING_PLAN_CREATE
            elif method == "PUT" or method == "PATCH":
                return ActivityActionType.TRAINING_PLAN_UPDATE
            elif method == "DELETE":
                return ActivityActionType.TRAINING_PLAN_DELETE
            elif method == "GET":
                return ActivityActionType.TRAINING_PLAN_VIEW
        
        # LLM Endpoints
        elif "/llm" in path or "/generate" in path:
            if "workout" in path:
                return ActivityActionType.LLM_WORKOUT_GENERATE
            elif "training-plan" in path:
                return ActivityActionType.LLM_TRAINING_PLAN_GENERATE
            else:
                return ActivityActionType.LLM_FEEDBACK_ANALYZE
        
        # Feedback Endpoints
        elif "/feedback" in path or "/app-feedback" in path:
            if method == "POST":
                return ActivityActionType.APP_FEEDBACK_CREATE
            elif method == "PUT" or method == "PATCH":
                return ActivityActionType.APP_FEEDBACK_UPDATE
        
        # Showcase Endpoints
        elif "/showcase" in path:
            if method == "POST":
                return ActivityActionType.SHOWCASE_TEMPLATE_CREATE
            elif method == "PUT" or method == "PATCH":
                return ActivityActionType.SHOWCASE_TEMPLATE_UPDATE
            elif method == "GET":
                return ActivityActionType.SHOWCASE_VIEW
        
        # Exercise Endpoints (falls separate)
        elif "/exercise" in path:
            if method == "POST":
                return ActivityActionType.EXERCISE_CREATE
            elif method == "PUT" or method == "PATCH":
                return ActivityActionType.EXERCISE_UPDATE
            elif method == "DELETE":
                return ActivityActionType.EXERCISE_DELETE
            elif method == "GET":
                return ActivityActionType.EXERCISE_VIEW
        
        # Error Handling
        if response.status_code >= 500:
            return ActivityActionType.API_ERROR
        elif response.status_code == 401:
            return ActivityActionType.UNAUTHORIZED_ACCESS_ATTEMPT
        elif response.status_code == 429:
            return ActivityActionType.RATE_LIMIT_EXCEEDED
        
        # Default fallback
        return ActivityActionType.API_ERROR
    
    def extract_resource_info(self, request: Request, response: Response) -> tuple[Optional[str], Optional[str]]:
        """
        Extrahiert Resource ID und Type aus Request/Response.
        """
        path_parts = request.url.path.strip("/").split("/")
        
        # Versuche Resource ID aus URL zu extrahieren
        resource_id = None
        resource_type = None
        
        # Pattern: /api/workouts/123 -> resource_id=123, resource_type=workout
        if len(path_parts) >= 2:
            for i, part in enumerate(path_parts):
                if part in ["workouts", "training-plan", "exercises", "users", "feedback"]:
                    resource_type = part.rstrip("s")  # workouts -> workout
                    if i + 1 < len(path_parts) and path_parts[i + 1].isdigit():
                        resource_id = path_parts[i + 1]
                    break
        
        # Versuche Resource ID aus Response Body zu extrahieren (bei POST)
        if not resource_id and request.method == "POST" and response.status_code in [200, 201]:
            try:
                # Response Body lesen (falls verfügbar)
                if hasattr(response, 'body'):
                    response_data = json.loads(response.body.decode())
                    if isinstance(response_data, dict):
                        resource_id = response_data.get('id') or response_data.get('resource_id')
            except Exception:
                pass
        
        return resource_id, resource_type

 