from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
from app.models.user_activity_log_model import ActivityActionType, RiskLevel

class UserActivityLogCreate(BaseModel):
    """Schema für die Erstellung eines User Activity Logs"""
    user_id_hash: Optional[str] = None
    session_id: Optional[str] = None
    endpoint: str
    http_method: str
    action_type: ActivityActionType
    resource_id: Optional[str] = None
    resource_type: Optional[str] = None
    request_data: Optional[Dict[str, Any]] = None
    response_status_code: int
    response_time_ms: Optional[int] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    risk_level: RiskLevel = RiskLevel.LOW
    risk_score: Optional[float] = 0.0
    risk_indicators: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None
    is_suspicious: bool = False
    is_automated: bool = False