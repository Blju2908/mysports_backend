from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.user_model import UserModel
from sqlmodel import select
from uuid import UUID

async def get_user_by_id(user_id: UUID, db: AsyncSession) -> UserModel | None:
    user_query = select(UserModel).where(UserModel.id == user_id)
    user_result = await db.exec(user_query)
    return user_result.first()

