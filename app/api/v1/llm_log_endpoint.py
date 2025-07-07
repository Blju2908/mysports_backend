from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime, timedelta
import calendar
from pydantic import BaseModel

from app.models.llm_call_log_model import LlmCallLog, LlmOperationStatus
from app.core.auth import get_current_user, User
from app.db.session import get_session

router = APIRouter(prefix="/llm-logs", tags=["llm-logs"])


class WorkoutUsageRequest(BaseModel):
    subscription_start: str


def calculate_current_billing_period(subscription_start: datetime, current_date: datetime = None):
    """
    Calculate the current monthly billing period based on subscription start date.
    
    Logic:
    - Monthly billing cycles start on the same day of month as subscription started
    - If subscription started on 31st and current month has fewer days, use last day of month
    
    Example:
    - Subscription started: July 2nd, 2024
    - Today: August 13th, 2024
    - Current period: August 2nd, 2024 00:00:00 - September 2nd, 2024 00:00:00 (exclusive)
    """
    if current_date is None:
        current_date = datetime.utcnow()
    
    # Extract the day of month from subscription start
    billing_day = subscription_start.day
    current_year = current_date.year
    current_month = current_date.month
    
    # Calculate the billing date for current month
    try:
        current_billing_start = current_date.replace(day=billing_day, hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        # Handle case where billing day doesn't exist in current month (e.g., Jan 31 -> Feb 31)
        last_day = calendar.monthrange(current_year, current_month)[1]
        current_billing_start = current_date.replace(day=last_day, hour=0, minute=0, second=0, microsecond=0)
    
    # If we haven't reached the billing day this month, current period started last month
    if current_date < current_billing_start:
        # Current period started last month
        if current_month == 1:
            prev_year = current_year - 1
            prev_month = 12
        else:
            prev_year = current_year
            prev_month = current_month - 1
            
        try:
            period_start = current_date.replace(year=prev_year, month=prev_month, day=billing_day, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            last_day = calendar.monthrange(prev_year, prev_month)[1]
            period_start = current_date.replace(year=prev_year, month=prev_month, day=last_day, hour=0, minute=0, second=0, microsecond=0)
            
        period_end = current_billing_start
    else:
        # Current period started this month
        period_start = current_billing_start
        
        # Calculate next month's billing date
        if current_month == 12:
            next_year = current_year + 1
            next_month = 1
        else:
            next_year = current_year
            next_month = current_month + 1
            
        try:
            period_end = current_date.replace(year=next_year, month=next_month, day=billing_day, hour=0, minute=0, second=0, microsecond=0)
        except ValueError:
            last_day = calendar.monthrange(next_year, next_month)[1]
            period_end = current_date.replace(year=next_year, month=next_month, day=last_day, hour=0, minute=0, second=0, microsecond=0)
    
    return period_start, period_end


@router.post("/workout-usage", response_model=Dict[str, Any])
async def get_workout_usage_stats(
    request: WorkoutUsageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get workout-related API usage statistics for the current user.
    
    Calculates usage for the current monthly billing period based on subscription start date.
    Each month the user gets 100 workout generations.
    
    Returns successful calls to llm/create-workout and workout/revise endpoints.
    """
    try:
        # Parse subscription start date
        subscription_start_date = datetime.fromisoformat(request.subscription_start.replace('Z', '+00:00')).replace(tzinfo=None)
        
        # Calculate current billing period
        start_date, end_date = calculate_current_billing_period(subscription_start_date)
        
        # Ensure user ID is a string (database expects VARCHAR)
        user_id_str = str(current_user.id)
        
        # Query for successful workout-related API calls in current billing period
        workout_endpoints = ['llm/start-workout-creation', 'llm/start-workout-revision']
        
        result = await db.execute(
            select(func.count(LlmCallLog.id)).where(
                and_(
                    LlmCallLog.user_id == user_id_str,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp < end_date,
                    LlmCallLog.status == LlmOperationStatus.SUCCESS,
                    LlmCallLog.endpoint_name.in_(workout_endpoints)
                )
            )
        )
        
        total_calls = result.scalar() or 0
        max_calls = 100  # Monthly limit
        remaining_calls = max(0, max_calls - total_calls)
        usage_percentage = (total_calls / max_calls * 100) if max_calls > 0 else 0
        
        # Determine usage status based on percentage
        if usage_percentage >= 75:
            usage_status = "critical"
        elif usage_percentage >= 25:
            usage_status = "warning"
        else:
            usage_status = "normal"
        
        return {
            "total_calls": total_calls,
            "max_calls": max_calls,
            "remaining_calls": remaining_calls,
            "usage_percentage": round(usage_percentage, 1),
            "status": usage_status,
            "period_start": start_date.isoformat(),
            "period_end": end_date.isoformat(),
            "period_type": "subscription_billing",
            "tracked_endpoints": workout_endpoints
        }
        
    except Exception as e:
        print(f"Error getting workout usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workout usage statistics"
        ) 