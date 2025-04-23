from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_async_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserCreate

router = APIRouter()

@router.post("/", response_model=UserRead)
async def create_user(user: UserCreate, session: AsyncSession = Depends(get_async_session)):
    db_user = User(username=user.username, email=user.email, hashed_password=user.password)
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user 