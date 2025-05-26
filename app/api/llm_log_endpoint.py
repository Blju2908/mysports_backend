from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, and_
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.models.llm_call_log_model import LlmCallLog
from app.schemas.llm_log_schema import (
    LlmCallLogResponseSchema,
    LlmCallLogSummarySchema,
    LlmCallLogFilterSchema
)
from app.core.auth import get_current_user, User
from app.db.session import get_session

router = APIRouter(prefix="/llm-logs", tags=["llm-logs"])


@router.get("/", response_model=List[LlmCallLogResponseSchema])
async def get_llm_logs(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    endpoint_name: Optional[str] = Query(None, description="Filter by endpoint name"),
    llm_operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_date: Optional[datetime] = Query(None, description="Filter from this date"),
    end_date: Optional[datetime] = Query(None, description="Filter until this date"),
    limit: int = Query(100, description="Maximum number of results"),
    offset: int = Query(0, description="Number of results to skip"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Retrieve LLM call logs with optional filtering.
    Only accessible by admin users or users viewing their own logs.
    """
    # Build query with filters
    query = select(LlmCallLog)
    
    # Security: Regular users can only see their own logs
    # TODO: Add admin check here when admin roles are implemented
    if user_id:
        # For now, only allow users to see their own logs
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own logs"
            )
        query = query.where(LlmCallLog.user_id == user_id)
    else:
        # If no user_id specified, show current user's logs
        query = query.where(LlmCallLog.user_id == current_user.id)
    
    # Apply additional filters
    if endpoint_name:
        query = query.where(LlmCallLog.endpoint_name.ilike(f"%{endpoint_name}%"))
    
    if llm_operation_type:
        query = query.where(LlmCallLog.llm_operation_type == llm_operation_type)
    
    if success is not None:
        query = query.where(LlmCallLog.success == success)
    
    if start_date:
        query = query.where(LlmCallLog.timestamp >= start_date)
    
    if end_date:
        query = query.where(LlmCallLog.timestamp <= end_date)
    
    # Order by timestamp descending (newest first)
    query = query.order_by(desc(LlmCallLog.timestamp))
    
    # Apply pagination
    query = query.offset(offset).limit(limit)
    
    try:
        result = await db.execute(query)
        logs = result.scalars().all()
        
        return [LlmCallLogResponseSchema.from_orm(log) for log in logs]
    
    except Exception as e:
        print(f"Error retrieving LLM logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving LLM logs"
        )


@router.get("/summary", response_model=LlmCallLogSummarySchema)
async def get_llm_logs_summary(
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    days: int = Query(7, description="Number of days to include in summary"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get a summary of LLM call statistics.
    """
    # Security: Regular users can only see their own stats
    if user_id and user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own statistics"
        )
    
    target_user_id = user_id or current_user.id
    
    # Calculate date range
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days)
    
    try:
        # Base query with date range and user filter
        base_query = select(LlmCallLog).where(
            and_(
                LlmCallLog.user_id == target_user_id,
                LlmCallLog.timestamp >= start_date,
                LlmCallLog.timestamp <= end_date
            )
        )
        
        # Total calls
        total_result = await db.execute(
            select(func.count(LlmCallLog.id)).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date
                )
            )
        )
        total_calls = total_result.scalar() or 0
        
        # Successful calls
        success_result = await db.execute(
            select(func.count(LlmCallLog.id)).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date,
                    LlmCallLog.success == True
                )
            )
        )
        successful_calls = success_result.scalar() or 0
        
        failed_calls = total_calls - successful_calls
        success_rate = (successful_calls / total_calls * 100) if total_calls > 0 else 0
        
        # Average duration
        duration_result = await db.execute(
            select(func.avg(LlmCallLog.duration_ms)).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date,
                    LlmCallLog.duration_ms.isnot(None)
                )
            )
        )
        average_duration = duration_result.scalar()
        
        # Most used endpoints
        endpoint_result = await db.execute(
            select(
                LlmCallLog.endpoint_name,
                func.count(LlmCallLog.id).label('count')
            ).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date
                )
            ).group_by(LlmCallLog.endpoint_name).order_by(desc('count')).limit(10)
        )
        most_used_endpoints = {row[0]: row[1] for row in endpoint_result.all()}
        
        # Operation types
        operation_result = await db.execute(
            select(
                LlmCallLog.llm_operation_type,
                func.count(LlmCallLog.id).label('count')
            ).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date,
                    LlmCallLog.llm_operation_type.isnot(None)
                )
            ).group_by(LlmCallLog.llm_operation_type).order_by(desc('count'))
        )
        operation_types = {row[0]: row[1] for row in operation_result.all()}
        
        # Error types
        error_result = await db.execute(
            select(
                LlmCallLog.error_type,
                func.count(LlmCallLog.id).label('count')
            ).where(
                and_(
                    LlmCallLog.user_id == target_user_id,
                    LlmCallLog.timestamp >= start_date,
                    LlmCallLog.timestamp <= end_date,
                    LlmCallLog.success == False,
                    LlmCallLog.error_type.isnot(None)
                )
            ).group_by(LlmCallLog.error_type).order_by(desc('count'))
        )
        error_types = {row[0]: row[1] for row in error_result.all()}
        
        return LlmCallLogSummarySchema(
            total_calls=total_calls,
            successful_calls=successful_calls,
            failed_calls=failed_calls,
            success_rate=round(success_rate, 2),
            average_duration_ms=round(average_duration, 2) if average_duration else None,
            most_used_endpoints=most_used_endpoints,
            operation_types=operation_types,
            error_types=error_types,
            date_range=f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
    
    except Exception as e:
        print(f"Error generating LLM logs summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error generating LLM logs summary"
        )


@router.get("/my-logs", response_model=List[LlmCallLogResponseSchema])
async def get_my_llm_logs(
    endpoint_name: Optional[str] = Query(None, description="Filter by endpoint name"),
    llm_operation_type: Optional[str] = Query(None, description="Filter by operation type"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    days: int = Query(7, description="Number of days to look back"),
    limit: int = Query(50, description="Maximum number of results"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Convenience endpoint for users to view their own recent LLM logs.
    """
    start_date = datetime.utcnow() - timedelta(days=days)
    
    return await get_llm_logs(
        user_id=current_user.id,
        endpoint_name=endpoint_name,
        llm_operation_type=llm_operation_type,
        success=success,
        start_date=start_date,
        end_date=None,
        limit=limit,
        offset=0,
        current_user=current_user,
        db=db
    )


@router.get("/my-summary", response_model=LlmCallLogSummarySchema)
async def get_my_llm_summary(
    days: int = Query(7, description="Number of days to include in summary"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Convenience endpoint for users to view their own LLM usage summary.
    """
    return await get_llm_logs_summary(
        user_id=current_user.id,
        days=days,
        current_user=current_user,
        db=db
    )


@router.get("/workout-usage", response_model=Dict[str, Any])
async def get_workout_usage_stats(
    period_start: Optional[datetime] = Query(None, description="Start of the billing period"),
    period_end: Optional[datetime] = Query(None, description="End of the billing period"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    """
    Get workout-related API usage statistics for the current user.
    Returns successful calls to llm/create-workout and workout/revise endpoints in the last 30 days.
    """
    try:
        # Use provided period or default to last 30 days
        if period_start and period_end:
            # Convert timezone-aware datetimes to naive UTC for database compatibility
            start_date = period_start.replace(tzinfo=None) if period_start.tzinfo else period_start
            end_date = period_end.replace(tzinfo=None) if period_end.tzinfo else period_end
        else:
            # Fallback to 30 days if no subscription period provided
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
                    LlmCallLog.success == True,
                    LlmCallLog.endpoint_name.in_(workout_endpoints)
                )
            )
        )
        
        total_calls = result.scalar() or 0
        max_calls = 100
        remaining_calls = max(0, max_calls - total_calls)
        usage_percentage = (total_calls / max_calls * 100) if max_calls > 0 else 0
        
        # Determine usage status based on percentage (renamed to avoid conflict)
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