from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.engine.result import ScalarResult  # Import for type hint clarity
from pydantic import BaseModel

from app.db.session import get_session
from app.models.showcase_feedback_model import Waitlist

router = APIRouter(prefix="/showcase")


class WaitlistCall(BaseModel):
    email: str


class WaitlistCountResponse(BaseModel):
    total_spots: int = 300
    used_spots: int
    remaining_spots: int


@router.post(
    "/waitlist",
    response_model=WaitlistCall,
    status_code=status.HTTP_201_CREATED,
    summary="Add an email to the waitlist",
    tags=["showcase"],
)
async def join_waitlist(
    *, session: AsyncSession = Depends(get_session), waitlist_data: WaitlistCall
) -> WaitlistCall:
    """
    Adds an email to the waitlist.
    """
    email = waitlist_data.email
    print(f"Adding email to waitlist: {email}")

    db_waitlist = Waitlist(email=waitlist_data.email)

    try:
        session.add(db_waitlist)
        await session.commit()
        await session.refresh(db_waitlist)
    except Exception as e:
        print(f"Error adding email to waitlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to add email to waitlist.")

    print(f"Added email to waitlist: {email}")

    return waitlist_data


@router.get(
    "/waitlist/count",
    response_model=WaitlistCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current waitlist statistics (used & remaining spots)",
    tags=["showcase"],
)
async def get_waitlist_count(
    *, session: AsyncSession = Depends(get_session)
) -> WaitlistCountResponse:
    """Return the number of emails currently on the waitlist and the remaining available beta spots."""
    try:
        statement = select(Waitlist)
        result: ScalarResult[Waitlist] = await session.exec(statement)
        used_spots = len(result.all())
    except Exception as e:
        print(f"Error fetching waitlist count: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch waitlist count.")

    total_spots = 300
    remaining_spots = max(total_spots - used_spots, 0)
    return WaitlistCountResponse(
        total_spots=total_spots,
        used_spots=used_spots,
        remaining_spots=remaining_spots,
    )
