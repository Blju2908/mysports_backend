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

class UserActivityLogResponse(BaseModel):
    """Schema für die Ausgabe eines User Activity Logs"""
    id: int
    user_id_hash: Optional[str]
    session_id: Optional[str]
    timestamp: datetime
    endpoint: str
    http_method: str
    action_type: ActivityActionType
    resource_id: Optional[str]
    resource_type: Optional[str]
    response_status_code: int
    response_time_ms: Optional[int]
    ip_address: Optional[str]
    user_agent: Optional[str]
    device_fingerprint: Optional[str]
    country_code: Optional[str]
    city: Optional[str]
    risk_level: RiskLevel
    risk_score: Optional[float]
    is_suspicious: bool
    is_automated: bool
    processed_at: Optional[datetime]

class UserActivityLogFilter(BaseModel):
    """Schema für die Filterung von User Activity Logs"""
    user_id_hash: Optional[str] = None
    action_type: Optional[ActivityActionType] = None
    risk_level: Optional[RiskLevel] = None
    is_suspicious: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    endpoint: Optional[str] = None
    ip_address: Optional[str] = None
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)

class UserActivitySummary(BaseModel):
    """Schema für Activity Summary"""
    user_id_hash: str
    total_activities: int
    suspicious_activities: int
    risk_score_avg: float
    last_activity: datetime
    most_common_actions: Dict[str, int]
    unique_ips: int
    unique_devices: int

class SecurityAlert(BaseModel):
    """Schema für Security Alerts"""
    alert_type: str
    user_id_hash: Optional[str]
    risk_level: RiskLevel
    description: str
    activity_log_id: int
    timestamp: datetime
    context_data: Optional[Dict[str, Any]] = None 