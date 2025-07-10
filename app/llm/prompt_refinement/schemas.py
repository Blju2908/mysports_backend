"""
Pydantic schemas for structured outputs from the prompt refinement agents.
"""

from pydantic import BaseModel, Field
from typing import List, Literal
from enum import Enum


class WeaknessCategory(str, Enum):
    """Categories for identified weaknesses"""
    TRAININGSLOGIK = "Trainingslogik"
    PERSONALISIERUNG = "Personalisierung"
    PROMPT_COMPLIANCE = "Prompt-Compliance"
    APP_VISION = "App-Vision"


class WeaknessItem(BaseModel):
    """Individual weakness identified by the critique agent"""
    category: WeaknessCategory = Field(description="Category of the weakness")
    issue: str = Field(description="Concrete description of the weakness")
    impact: str = Field(description="Why this is problematic")
    prompt_fix: str = Field(description="How to fix this in the system prompt")


class CritiqueResponse(BaseModel):
    """Structured response from the critique agent"""
    overall_score: int = Field(ge=1, le=10, description="Overall score from 1-10")
    strengths: List[str] = Field(description="List of concrete strengths")
    weaknesses: List[WeaknessItem] = Field(description="List of identified weaknesses")
    key_improvements: List[str] = Field(description="Most important improvements needed")


class ValidationDecision(str, Enum):
    """Possible validation decisions"""
    WORKOUT_1 = "WORKOUT_1"
    WORKOUT_2 = "WORKOUT_2"
    TIE = "TIE"


class ValidationResponse(BaseModel):
    """Response from the validation agent"""
    reasoning: str = Field(description="2-3 sentence reasoning for the decision")
    decision: ValidationDecision = Field(description="Final decision on which workout is better")


class RefinedPrompts(BaseModel):
    """Structured response from the refine agent with both prompt parts."""
    prompt_template: str = Field(description="The full, revised text for the prompt template (workout_generation_prompt_step1.md).")
    training_principles: str = Field(description="The full, revised text for the training principles (training_principles_base.md).")


# Configuration models
class RefinementConfig(BaseModel):
    """Configuration for the refinement process"""
    max_iterations: int = Field(default=5, ge=1, le=20)
    provider: Literal["openai", "anthropic", "google"] = Field(default="openai")
    model_name: str = Field(default="gpt-4o")
    use_production_db: bool = Field(default=False)
    save_iterations: bool = Field(default=True)
    user_id: str = Field(description="User ID for testing")


class IterationResult(BaseModel):
    """Result of a single refinement iteration"""
    iteration: int
    original_prompt: str
    critique: CritiqueResponse
    refined_prompt: str
    original_workout: str
    refined_workout: str
    validation: ValidationResponse
    improved: bool
    timestamp: str 