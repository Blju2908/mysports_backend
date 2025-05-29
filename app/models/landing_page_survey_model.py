from typing import Optional, List
from sqlmodel import SQLModel, Field
from datetime import datetime
import json

class LandingPageSurvey(SQLModel, table=True):
    __tablename__ = "landing_page_surveys"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(max_length=255, index=True)
    name: Optional[str] = Field(default=None, max_length=255)
    training_goals: Optional[str] = Field(default=None, description="JSON array of training goals")
    training_types: Optional[str] = Field(default=None, description="JSON array of training types")
    current_apps: Optional[str] = Field(default=None, description="JSON array of current apps")
    comment: Optional[str] = Field(default=None)
    price_willingness: Optional[str] = Field(default=None, max_length=50)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "name": self.name,
            "training_goals": json.loads(self.training_goals) if self.training_goals else [],
            "training_types": json.loads(self.training_types) if self.training_types else [],
            "current_apps": json.loads(self.current_apps) if self.current_apps else [],
            "comment": self.comment,
            "price_willingness": self.price_willingness,
            "created_at": self.created_at.isoformat() if self.created_at else None
        } 