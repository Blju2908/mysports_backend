from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from uuid import UUID
from datetime import datetime

class WorkoutFeedback(SQLModel, table=True):
    __tablename__ = "workout_feedback"
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_id: int = Field(foreign_key="workouts.id", ondelete="CASCADE")
    user_id: UUID = Field(foreign_key="users.id", ondelete="CASCADE")
    rating: int = Field(..., ge=1, le=5)  # 1-5 Sterne
    duration_rating: int = Field(..., ge=-5, le=5)  # -5 bis +5 (zu kurz bis zu lang)
    intensity_rating: int = Field(..., ge=-5, le=5)  # -5 bis +5 (zu leicht bis zu schwer) 
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow) 