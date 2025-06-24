from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID

class WorkoutFeedbackSchema(BaseModel):
    workout_id: int
    rating: int = Field(..., ge=1, le=5)
    duration_rating: int = Field(..., ge=-5, le=5)
    intensity_rating: int = Field(..., ge=-5, le=5)
    comment: Optional[str] = None
    
class WorkoutFeedbackResponseSchema(WorkoutFeedbackSchema):
    """
    ✅ CLEAN RESPONSE SCHEMA: Nur workout_id als Identifier - keine interne feedback ID!
    Das Frontend braucht nur die workout_id, um das Feedback zu identifizieren.
    """
    user_id: UUID  # ✅ UUID Type matching the database model
    created_at: datetime
    
    class Config:
        from_attributes = True  # ✅ SQLModel Auto-Serialization! 