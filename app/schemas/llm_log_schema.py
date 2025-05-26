from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import BaseModel


class LlmCallLogResponseSchema(BaseModel):
    """Schema für die Response von LLM Call Logs."""
    
    id: int
    user_id: str
    endpoint_name: str
    method: str
    timestamp: datetime
    duration_ms: Optional[int]
    success: bool
    http_status_code: Optional[int]
    error_message: Optional[str]
    error_type: Optional[str]
    request_data: Optional[Dict[str, Any]]
    response_summary: Optional[str]
    llm_operation_type: Optional[str]
    workout_id: Optional[int]
    training_plan_id: Optional[int]
    user_agent: Optional[str]
    ip_address: Optional[str]
    
    class Config:
        from_attributes = True


class LlmCallLogSummarySchema(BaseModel):
    """Schema für zusammengefasste LLM Log-Statistiken."""
    
    total_calls: int
    successful_calls: int
    failed_calls: int
    success_rate: float
    average_duration_ms: Optional[float]
    most_used_endpoints: Dict[str, int]
    operation_types: Dict[str, int]
    error_types: Dict[str, int]
    date_range: str


class LlmCallLogFilterSchema(BaseModel):
    """Schema für Filter-Parameter beim Abrufen von Logs."""
    
    user_id: Optional[str] = None
    endpoint_name: Optional[str] = None
    llm_operation_type: Optional[str] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = 100
    offset: int = 0 