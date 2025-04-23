from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie, Request, BackgroundTasks, Query
from sqlmodel import Session, select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_async_session
from app.models.user_model import User
from app.schemas.user_schema import UserCreate, UserRead, LoginSchema
from app.core.security import get_password_hash, verify_password, create_access_token, decode_access_token
from app.core.email import send_verification_email, send_password_reset_email
from pydantic import EmailStr, BaseModel
from datetime import timedelta

# TODO: Implement CSRF-Schutz

router = APIRouter()

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordUpdateRequest(BaseModel):
    token: str
    new_password: str

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == user.email))
    existing_user = result.scalars().first()
    if existing_user:
        raise HTTPException(status_code=400, detail="E-Mail already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True,  # User ist aktiv, aber noch nicht verifiziert
        is_verified=False
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    # Verifizierungs-Token generieren
    token = create_access_token({"sub": str(db_user.id)}, expires_delta=timedelta(hours=1))
    await send_verification_email(db_user.email, db_user.email, token, background_tasks)
    return db_user

@router.post("/login", response_model=UserRead)
async def login_user(
    response: Response,
    user: LoginSchema,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == user.email))
    db_user = result.scalars().first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_access_token({"sub": str(db_user.id)})
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # In Produktion: True!
        samesite="lax",
        max_age=60*60*24  # 24h
    )
    return db_user

@router.get("/me", response_model=UserRead)
async def get_me(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    access_token: str = Cookie(default=None)
):
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(access_token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user_id = int(payload["sub"])
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=401, detail="User not found")
    return db_user

@router.post("/logout")
def logout_user(response: Response):
    response.set_cookie(
        key="access_token",
        value="",
        httponly=True,
        secure=False,  # In Produktion: True!
        samesite="lax",
        max_age=0
    )
    return {"message": "Logout successful"}

@router.get("/verify-email")
async def verify_email(token: str = Query(...), session: AsyncSession = Depends(get_async_session)):
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = int(payload["sub"])
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.is_verified:
        return {"message": "E-Mail already verified"}
    db_user.is_verified = True
    session.add(db_user)
    await session.commit()
    return {"message": "E-Mail successfully verified"}

@router.post("/resend-verification")
async def resend_verification(
    email: EmailStr,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == email))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    if db_user.is_verified:
        return {"message": "E-Mail already verified"}
    token = create_access_token({"sub": str(db_user.id)}, expires_delta=timedelta(hours=1))
    await send_verification_email(db_user.email, db_user.email, token, background_tasks)
    return {"message": "Verification e-mail sent"}

@router.post("/reset-password")
async def reset_password(
    data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_async_session)
):
    result = await session.execute(select(User).where(User.email == data.email))
    db_user = result.scalars().first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    token = create_access_token({"sub": str(db_user.id)}, expires_delta=timedelta(hours=1))
    await send_password_reset_email(db_user.email, db_user.email, token, background_tasks)
    return {"message": "Password reset e-mail sent"}

@router.post("/update-password")
async def update_password(
    data: PasswordUpdateRequest,
    session: AsyncSession = Depends(get_async_session)
):
    payload = decode_access_token(data.token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    user_id = int(payload["sub"])
    db_user = await session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    db_user.hashed_password = get_password_hash(data.new_password)
    session.add(db_user)
    await session.commit()
    return {"message": "Password updated successfully"} 