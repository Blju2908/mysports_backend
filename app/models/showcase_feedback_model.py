from typing import Optional
from sqlmodel import SQLModel, Field

class Waitlist(SQLModel, table=True):
    """Stores user information for the waitlist."""
    __tablename__ = "showcase_waitlist"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, description="User's email address")
