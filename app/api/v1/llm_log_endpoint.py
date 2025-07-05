from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime, timedelta
import calendar

from app.models.llm_call_log_model import LlmCallLog
from app.core.auth import get_current_user, User
from app.db.session import get_session

router = APIRouter(prefix="/llm-logs", tags=["llm-logs"])


def calculate_current_billing_period(subscription_start: datetime, current_date: datetime = None):
    """
    Calculate the current monthly billing period based on subscription start date.
    
    Logic:
    - Monthly billing cycles start on the same day of month as subscription started
    - For annual subscriptions, we still bill monthly but track the full year
    - If subscription started on 31st and current month has fewer days, use last day of month
    
    Example:
    - Subscription started: July 2nd
    - Today: August 13th  
    - Current period: August 2nd - September 2nd (exclusive)
    """
    if current_date is None:
        current_date = datetime.utcnow()
    
    # Extract the day of month from subscription start
    billing_day = subscription_start.day
    current_year = current_date.year
    current_month = current_date.month
    
    # Calculate the billing date for current month (at start of day, not current time)
    try:
        current_billing_start = current_date.replace(day=billing_day, hour=0, minute=0, second=0, microsecond=0)
    except ValueError:
        # Handle case where billing day doesn't exist in current month (e.g., Jan 31 -> Feb 31)
        # Use the last day of the current month instead
        last_day = calendar.monthrange(current_year, current_month)[1]
        current_billing_start = current_date.replace(day=last_day, hour=0, minute=0, second=0, microsecond=0)
    
    # If we haven't reached the billing day this month, use previous month's billing period
    if current_date.day < billing_day:
        # We're before the billing day this month, so current period started last month
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
        # We're on or after the billing day this month, so current period started this month
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


@router.get("/workout-usage", response_model=Dict[str, Any])
async def get_workout_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
    subscription_start: str = None,
):
    """
    Get workout-related API usage statistics for the current user.
    Can use either:
    - Subscription-based billing period (recommended): monthly cycles based on subscription start date
    - Custom period: fixed period based on provided start/end dates  
    - Rolling 30-day window (fallback): older calls automatically drop out as time progresses
    
    For subscription billing:
    - Monthly subscriptions: count usage in current monthly billing cycle
    - Annual subscriptions: also use monthly billing cycles (e.g., July 2 - August 2)
    
    Returns successful calls to llm/create-workout and workout/revise endpoints.
    """
    try:
        # Use subscription-based billing or fallback to rolling window
        if subscription_start:
            # Subscription-based billing: simple monthly period from subscription start
            subscription_start_date = datetime.fromisoformat(subscription_start.replace('Z', '+00:00')).replace(tzinfo=None)
            
            # Simple approach: subscription start + 1 month
            start_date = subscription_start_date
            # Add 1 month to get end date
            if subscription_start_date.month == 12:
                end_date = subscription_start_date.replace(year=subscription_start_date.year + 1, month=1)
            else:
                end_date = subscription_start_date.replace(month=subscription_start_date.month + 1)
            
            period_type = "subscription_billing"
        else:
            # Fallback: Rolling 30-day window for users without subscription data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            period_type = "rolling_30_days"
        
        # Ensure user ID is a string (database expects VARCHAR)
        user_id_str = str(current_user.id)
        
        # Query for successful workout-related API calls
        workout_endpoints = ['llm/create-workout', 'workout/revise']
        
        # Query for successful workout-related API calls
        result = await db.execute(
            select(func.count(LlmCallLog.id)).where(
                and_(
                    LlmCallLog.user_id == user_id_str,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp < end_date,  # Use < instead of <= for exclusive end date
                    LlmCallLog.success == True,  # Explicit boolean comparison
                    LlmCallLog.endpoint_name.in_(workout_endpoints)
                )
            )
        )
        
        total_calls = result.scalar() or 0
        max_calls = 100
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
            "period_type": period_type,
            "tracked_endpoints": workout_endpoints
        }
        
    except Exception as e:
        print(f"Error getting workout usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workout usage statistics"
        ) 