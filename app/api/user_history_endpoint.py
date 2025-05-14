# from fastapi import APIRouter, Depends, HTTPException, status
# from sqlalchemy.ext.asyncio import AsyncSession
# from sqlalchemy import select, delete
# from typing import List, Optional
# from datetime import datetime
# from pydantic import BaseModel, Field, ConfigDict
# import uuid
# from sqlalchemy.orm import selectinload
# from datetime import date

# from app.core.auth import get_current_user, User
# from app.db.session import get_session
# from app.models.training_history import ActivityLog

# router = APIRouter(tags=["user-history"])

# # Define schemas for the ActivityLog
# class ActivityLogSchema(BaseModel):
#     id: int
#     exercise_name: str
#     timestamp: datetime
#     weight: Optional[float] = None
#     reps: Optional[int] = None
#     duration: Optional[int] = None
#     distance: Optional[float] = None
#     notes: Optional[str] = None

#     model_config = ConfigDict(from_attributes=True)

# class ManualActivityLogCreateSchema(BaseModel):
#     exercise_name: str = Field(..., description="Name der Aktivität")
#     notes: str = Field(..., description="Beschreibung der Aktivität")
#     timestamp: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Zeitpunkt der Aktivität")

# @router.get("/", response_model=List[ActivityLogSchema])
# async def get_user_history(
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
#     from_date: Optional[date] = None,
#     to_date: Optional[date] = None,
# ):
#     """
#     Get all activity logs for the current user.
#     Optionally filter by date range.
#     """
    
#     print(f"Current user: {current_user.id}")
#     query = select(ActivityLog).where(ActivityLog.user_id == current_user.id)
    
#     # Apply date filters if provided
#     if from_date:
#         query = query.where(ActivityLog.timestamp >= datetime.combine(from_date, datetime.min.time()))
#     if to_date:
#         query = query.where(ActivityLog.timestamp <= datetime.combine(to_date, datetime.max.time()))
    
#     # Order by timestamp descending (newest first)
#     query = query.order_by(ActivityLog.timestamp.desc())
    
#     result = await db.execute(query)
#     logs = result.scalars().all()
    
#     return logs

# @router.delete("/{log_id}", status_code=204)
# async def delete_history_entry(
#     log_id: int,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Delete a specific activity log entry.
#     Ensures the entry belongs to the current user.
#     """
#     # Check if the log exists and belongs to the user
#     log_query = select(ActivityLog).where(
#         ActivityLog.id == log_id,
#         ActivityLog.user_id == current_user.id
#     )
#     result = await db.execute(log_query)
#     log = result.scalar_one_or_none()
    
#     if not log:
#         raise HTTPException(
#             status_code=status.HTTP_404_NOT_FOUND,
#             detail="Log entry not found or you don't have permission to delete it."
#         )
    
#     # Delete the log
#     delete_query = delete(ActivityLog).where(
#         ActivityLog.id == log_id,
#         ActivityLog.user_id == current_user.id
#     )
#     await db.execute(delete_query)
    
#     try:
#         await db.commit()
#         return None
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Failed to delete history entry: {str(e)}"
#         )

# @router.post("/", status_code=201)
# async def add_manual_activity_log(
#     payload: ManualActivityLogCreateSchema,
#     db: AsyncSession = Depends(get_session),
#     current_user: User = Depends(get_current_user),
# ):
#     """
#     Füge einen manuellen Aktivitäts-Eintrag für den aktuellen User hinzu.
#     """
#     new_log = ActivityLog(
#         user_id=current_user.id,
#         exercise_name=payload.exercise_name,
#         notes=payload.notes,
#         timestamp=payload.timestamp,
#     )
#     db.add(new_log)
#     try:
#         await db.commit()
#         await db.refresh(new_log)
#         return {"success": True, "id": new_log.id}
#     except Exception as e:
#         await db.rollback()
#         raise HTTPException(
#             status_code=500,
#             detail=f"Fehler beim Speichern des Aktivitäts-Eintrags: {str(e)}"
#         ) 