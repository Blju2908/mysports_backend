from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
import json

from app.db.session import get_session
from app.models.landing_page_survey_model import LandingPageSurvey
from app.schemas.landing_page_survey_schema import (
    LandingPageSurveyCreateSchema,
    LandingPageSurveySuccessSchema
)

router = APIRouter()

@router.post("/survey", response_model=LandingPageSurveySuccessSchema, status_code=status.HTTP_201_CREATED)
async def create_landing_page_survey(
    survey_data: LandingPageSurveyCreateSchema,
    db: AsyncSession = Depends(get_session)
):
    """
    Landing Page Survey erstellen - kein Auth erforderlich.
    """
    try:
        # Survey erstellen mit JSON-Serialisierung für Arrays
        survey = LandingPageSurvey(
            email=survey_data.email,
            name=survey_data.name,
            training_goals=json.dumps(survey_data.training_goals) if survey_data.training_goals else None,
            training_types=json.dumps(survey_data.training_types) if survey_data.training_types else None,
            current_apps=json.dumps(survey_data.current_apps) if survey_data.current_apps else None,
            comment=survey_data.comment,
            price_willingness=survey_data.price_willingness,
            created_at=datetime.utcnow()
        )
        
        db.add(survey)
        await db.commit()
        await db.refresh(survey)
        
        return LandingPageSurveySuccessSchema(
            success=True,
            message="Survey erfolgreich gespeichert! Vielen Dank für dein Feedback.",
            survey_id=survey.id
        )
        
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Exception in create_landing_page_survey: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Speichern der Survey: {str(e)}"
        ) 