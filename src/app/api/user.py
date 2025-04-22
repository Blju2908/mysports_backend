from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.db.session import get_session
from app.models.user_model import User
from app.schemas.user_schema import UserRead, UserCreate

router = APIRouter()

@router.post("/", response_model=UserRead)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    db_user = User(username=user.username, email=user.email, hashed_password=user.password)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user 