from uuid import UUID
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.models.training_history import ActivityLog

async def get_training_history_for_user(user_id: UUID, db: AsyncSession, history_length: int = 100) -> ActivityLog | None:
    query = (
        select(ActivityLog)
        .where(ActivityLog.user_id == user_id)
        .order_by(ActivityLog.timestamp.desc())
        .limit(history_length)
    )
    result = await db.exec(query)
    return result.all()
