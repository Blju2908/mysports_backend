from typing import Optional, List, Dict, Any, TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship, Column
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

if TYPE_CHECKING:
    from .workout_model import Workout
    # Forward reference for the not-yet-implemented training plan model
    # Assuming it will be in a file named 'showcase_training_plan_model.py'
    # or adjust the import path as needed.
    # from .showcase_training_plan_model import ShowcaseTrainingPlan 

class ShowcaseFeedback(SQLModel, table=True):
    """Stores the complete feedback session for a user showcase interaction."""
    __tablename__ = "showcase_feedbacks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    questionnaire_template_id: Optional[int] = Field(default=None, foreign_key="showcase_questionnaire_templates.id")
    workout_id: Optional[int] = Field(default=None, foreign_key="workouts.id")
    training_plan_id: Optional[int] = Field(default=None, foreign_key="showcase_training_plans.id")
    answers: Optional[Dict[str, Any]] = Field(default=None, sa_column=Column(JSONB))
    feedback_comment: Optional[str] = Field(default=None, description="User's textual feedback")
    feedback_rating: Optional[int] = Field(default=None, description="User rating (1-5 stars)")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"onupdate": datetime.utcnow})


    questionnaire_template: Optional["ShowcaseQuestionnaireTemplate"] = Relationship(back_populates="feedbacks")
    
    # workout: Optional["Workout"] = Relationship(back_populates="feedbacks") # Assuming Workout model has 'feedbacks' relation

    # Relationship to ShowcaseTrainingPlan (uncomment when model exists)
    # training_plan: Optional["ShowcaseTrainingPlan"] = Relationship(back_populates="feedbacks") # Assuming relation name

class ShowcaseTrainingPlan(SQLModel, table=True):
    __tablename__ = "showcase_training_plans"
    id: Optional[int] = Field(default=None, primary_key=True)
    goal: str
    restrictions: str
    equipment: str
    session_duration: str
    history: str

class ShowcaseQuestionnaireTemplate(SQLModel, table=True):
    """
    Stores the structure of a specific version of a questionnaire.
    """
    __tablename__ = "showcase_questionnaire_templates"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    questionnaire_id: str = Field(index=True, unique=True, description="Unique identifier string for the questionnaire version (e.g., 'q_v1.1')")
    questions: List[Dict[str, Any]] = Field(..., sa_column=Column(JSONB), description="The list of questions and their options for this template version")
    description: Optional[str] = Field(default=None, description="Optional description for this questionnaire template")
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    updated_at: datetime = Field(default_factory=datetime.utcnow, nullable=False, sa_column_kwargs={"onupdate": datetime.utcnow})

    # Relationship to feedbacks submitted using this template
    feedbacks: List["ShowcaseFeedback"] = Relationship(back_populates="questionnaire_template")
    
    
class Waitlist(SQLModel, table=True):
    """Stores user information for the waitlist."""
    __tablename__ = "showcase_waitlist"

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True, description="User's email address")
