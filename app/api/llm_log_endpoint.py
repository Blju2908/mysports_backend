from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_
from typing import Dict, Any
from datetime import datetime, timedelta

from app.models.llm_call_log_model import LlmCallLog
from app.core.auth import get_current_user, User
from app.db.session import get_session

router = APIRouter(prefix="/llm-logs", tags=["llm-logs"])


@router.get("/workout-usage", response_model=Dict[str, Any])
async def get_workout_usage_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get workout-related API usage statistics for the current user.
    Uses a rolling 30-day window - older calls automatically drop out as time progresses.
    Returns successful calls to llm/create-workout and workout/revise endpoints.
    """
    try:
        # Rolling 30-day window: from exactly 30 days ago until now
        # This means the count changes every day as old calls drop out
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        # Query for successful workout-related API calls
        workout_endpoints = ['llm/create-workout', 'workout/revise']
        
        result = await db.execute(
            select(func.count(LlmCallLog.id)).where(
                and_(
                    LlmCallLog.user_id == current_user.id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date,
                    LlmCallLog.success,
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
            "tracked_endpoints": workout_endpoints
        }
        
    except Exception as e:
        print(f"Error getting workout usage stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving workout usage statistics"
        ) 