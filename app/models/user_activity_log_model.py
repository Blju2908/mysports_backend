from typing import Optional, Dict, Any
from sqlmodel import SQLModel, Field, Column, JSON
from datetime import datetime
from uuid import UUID
import enum

class ActivityActionType(str, enum.Enum):
    # Authentication Actions
    LOGIN_SUCCESS = "auth_login_success"
    LOGIN_FAILED = "auth_login_failed"
    LOGOUT = "auth_logout"
    REGISTER_SUCCESS = "auth_register_success"
    REGISTER_FAILED = "auth_register_failed"
    OTP_REQUEST = "auth_otp_request"
    OTP_VERIFY_SUCCESS = "auth_otp_verify_success"
    OTP_VERIFY_FAILED = "auth_otp_verify_failed"
    PASSWORD_CHANGE = "auth_password_change"
    EMAIL_CHANGE = "auth_email_change"
    TOKEN_REFRESH = "auth_token_refresh"
    
    # Workout Actions
    WORKOUT_CREATE = "workout_create"
    WORKOUT_UPDATE = "workout_update"
    WORKOUT_DELETE = "workout_delete"
    WORKOUT_VIEW = "workout_view"
    WORKOUT_START = "workout_start"
    WORKOUT_FINISH = "workout_finish"
    WORKOUT_PAUSE = "workout_pause"
    WORKOUT_RESUME = "workout_resume"
    
    # Training Plan Actions
    TRAINING_PLAN_CREATE = "training_plan_create"
    TRAINING_PLAN_UPDATE = "training_plan_update"
    TRAINING_PLAN_DELETE = "training_plan_delete"
    TRAINING_PLAN_VIEW = "training_plan_view"
    TRAINING_PLAN_ASSIGN = "training_plan_assign"
    
    # Exercise Actions
    EXERCISE_CREATE = "exercise_create"
    EXERCISE_UPDATE = "exercise_update"
    EXERCISE_DELETE = "exercise_delete"
    EXERCISE_VIEW = "exercise_view"
    
    # Set Actions
    SET_CREATE = "set_create"
    SET_UPDATE = "set_update"
    SET_DELETE = "set_delete"
    SET_COMPLETE = "set_complete"
    
    # LLM Actions
    LLM_WORKOUT_GENERATE = "llm_workout_generate"
    LLM_TRAINING_PLAN_GENERATE = "llm_training_plan_generate"
    LLM_FEEDBACK_ANALYZE = "llm_feedback_analyze"
    LLM_PROMPT_INJECTION_DETECTED = "llm_prompt_injection_detected"
    
    # Feedback Actions
    APP_FEEDBACK_CREATE = "app_feedback_create"
    APP_FEEDBACK_UPDATE = "app_feedback_update"
    WORKOUT_FEEDBACK_CREATE = "workout_feedback_create"
    SHOWCASE_FEEDBACK_CREATE = "showcase_feedback_create"
    
    # Showcase Actions
    SHOWCASE_VIEW = "showcase_view"
    SHOWCASE_TEMPLATE_CREATE = "showcase_template_create"
    SHOWCASE_TEMPLATE_UPDATE = "showcase_template_update"
    
    # Security Actions
    SUSPICIOUS_ACTIVITY_DETECTED = "security_suspicious_activity"
    RATE_LIMIT_EXCEEDED = "security_rate_limit_exceeded"
    UNAUTHORIZED_ACCESS_ATTEMPT = "security_unauthorized_access"
    
    # System Actions
    API_ERROR = "system_api_error"
    API_TIMEOUT = "system_api_timeout"

class RiskLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class UserActivityLog(SQLModel, table=True):
    """
    Model für das Logging aller User-Aktivitäten in der App.
    Erfasst sowohl normale Aktionen als auch verdächtige Aktivitäten für Fraud Prevention.
    """
    
    __tablename__ = "user_activity_logs"
    
    id: int = Field(primary_key=True)
    
    # User Information (anonymized for privacy)
    user_id_hash: Optional[str] = Field(max_length=64, index=True, description="Anonymized user ID hash")
    session_id: Optional[str] = Field(max_length=255, index=True, description="Session identifier")
    
    # Timestamp Information
    timestamp: datetime = Field(default_factory=datetime.utcnow, index=True)
    
    # Request Information
    endpoint: str = Field(max_length=255, description="API endpoint path")
    http_method: str = Field(max_length=10, description="HTTP method (GET, POST, etc.)")
    
    # Activity Information
    action_type: ActivityActionType = Field(description="Type of action performed")
    resource_id: Optional[str] = Field(max_length=255, description="ID of affected resource")
    resource_type: Optional[str] = Field(max_length=100, description="Type of affected resource")
    
    # Request Details
    request_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Sanitized request data")
    response_status_code: int = Field(description="HTTP response status code")
    response_time_ms: Optional[int] = Field(description="Response time in milliseconds")
    
    # Security & Network Information
    ip_address: Optional[str] = Field(max_length=45, index=True, description="Client IP address")
    user_agent: Optional[str] = Field(max_length=500, description="Client user agent")
    device_fingerprint: Optional[str] = Field(max_length=255, description="Device fingerprint hash")
    
    # Geolocation (optional)
    country_code: Optional[str] = Field(max_length=2, description="Country code from IP")
    city: Optional[str] = Field(max_length=100, description="City from IP")
    
    # Risk Assessment
    risk_level: RiskLevel = Field(default=RiskLevel.LOW, description="Calculated risk level")
    risk_score: Optional[float] = Field(default=0.0, description="Numerical risk score (0.0-1.0)")
    risk_indicators: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Risk indicators detected")
    
    # Error Information
    error_message: Optional[str] = Field(max_length=1000, description="Error message if action failed")
    
    # Additional Context
    context_data: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSON), description="Additional context data")
    
    # Flags
    is_suspicious: bool = Field(default=False, index=True, description="Flagged as suspicious activity")
    is_automated: bool = Field(default=False, description="Detected as automated/bot activity")
    
    # Processing Information
    processed_at: Optional[datetime] = Field(default=None, description="When the log was processed for analysis")
    
    class Config:
        use_enum_values = True 