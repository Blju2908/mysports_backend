from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class ShowcaseQuestionnaireBase(BaseModel):
    """Base schema, might be useful later"""
    pass

class ShowcaseQuestionnaireResponse(ShowcaseQuestionnaireBase):
    """
    Schema for the response when fetching a specific questionnaire template.
    Matches the frontend's QuestionsResponse interface.
    """
    # questionnaireId: str = Field(alias='questionnaire_id') # Use alias if needed, Pydantic v2 often handles this
    questionnaire_id: str # Use model attribute name directly if from_attributes=True works
    questions: List[Dict[str, Any]] # Keep simple for now, matches JSONB structure

    class Config:
        from_attributes = True 
        populate_by_name = True # Handles camelCase from frontend potentially

# --- Schemas for Showcase Feedback ---

class ShowcaseFeedbackBase(BaseModel):
    """Base schema for feedback data."""
    answers: Optional[Dict[str, Any]] = None
    feedback_comment: Optional[str] = None

class ShowcaseFeedbackCreate(BaseModel):
    """Schema for receiving initial questionnaire answers."""
    questionnaireId: str # Frontend sends camelCase
    answers: Dict[str, Any]

    class Config:
        populate_by_name = True # Allows mapping questionnaireId to potential model field

class ShowcaseFeedbackUpdate(BaseModel):
    """Schema for updating questionnaire answers (or other feedback later)."""
    # Include questionnaireId if the frontend sends it during update
    questionnaireId: str 
    answers: Dict[str, Any]

    class Config:
        populate_by_name = True

class ShowcaseFeedbackResponse(ShowcaseFeedbackBase):
    """Schema for returning feedback data, including the generated ID."""
    id: int
    questionnaire_template_id: Optional[int] = None
    workout_id: Optional[int] = None
    feedback_rating: Optional[int] = None
    # training_plan_id: Optional[int] = None # Add when model relationship is active
    created_at: datetime
    updated_at: datetime
    
    # Map the model's 'id' to 'feedbackId' for the response if needed by frontend
    # feedbackId: int = Field(alias="id") 

    class Config:
        from_attributes = True
        # If using alias:
        # populate_by_name = True 

# --- Schemas for Showcase Training Plan ---

class ShowcaseTrainingPlanBase(BaseModel):
    """Base schema mirroring ShowcaseTrainingPlan model fields."""
    goal: str
    restrictions: str
    equipment: str
    session_duration: str 
    history: str

class ShowcaseTrainingPlanCreate(ShowcaseTrainingPlanBase):
    feedbackId: Optional[int] = None # ID of the ShowcaseFeedback to link to (optional)

class ShowcaseTrainingPlanResponse(ShowcaseTrainingPlanBase):
    """Schema for returning the created training plan."""
    id: int

    class Config:
        from_attributes = True

# --- TEMPORARY Schema for Fake Workout Response ---
# To match frontend expectations during development before actual workout generation

class WorkoutDataSchema(BaseModel):
    """Represents the structure of the nested workout data."""
    warmup: str
    main: str
    cooldown: str
    # createdAt: Optional[int] = None # Optional, match MSW if needed

class FakeWorkoutResponse(BaseModel):
    """Temporary response model for the training plan endpoint, returning a fake workout."""
    workoutId: str
    workout: WorkoutDataSchema

    class Config:
        from_attributes = True # Allow creating from objects if needed later

# You might add other showcase-related schemas here later
