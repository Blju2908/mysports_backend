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
    id: int
    user_id: str  # Explizit als String definiert (nicht UUID), damit FastAPI die UUID automatisch konvertiert
    created_at: datetime
    
    class Config:
        from_attributes = True
        
        # Modell-Validierungsfunktion für UUID-Konvertierung
        @classmethod
        def model_validate(cls, obj, *args, **kwargs):
            if hasattr(obj, "user_id") and isinstance(obj.user_id, UUID):
                obj.user_id = str(obj.user_id)
            return super().model_validate(obj, *args, **kwargs) 