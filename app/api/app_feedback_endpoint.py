from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import select
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.core.auth import get_current_user, User
from app.models.app_feedback_model import AppFeedbackModel
from app.models.user_model import UserModel
from app.schemas.app_feedback_schema import (
    AppFeedbackCreateSchema, 
    AppFeedbackResponseSchema, 
    AppFeedbackUpdateSchema,
    AppFeedbackListResponseSchema,
    AppFeedbackSuccessSchema
)

router = APIRouter(prefix="/feedback", tags=["App Feedback"])

@router.post("/", response_model=AppFeedbackSuccessSchema, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: AppFeedbackCreateSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Neues App-Feedback erstellen.
    Nutzer wird automatisch aus dem JWT Token extrahiert.
    """
    try:
        user_uuid = UUID(current_user.id)
        
        # Prüfen ob User existiert, falls nicht anlegen
        user_query = select(UserModel).where(UserModel.id == user_uuid)
        result = await db.execute(user_query)
        user = result.scalar_one_or_none()
        
        if not user:
            user = UserModel(id=user_uuid)
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        # Feedback erstellen
        feedback = AppFeedbackModel(
            user_id=user_uuid,
            feedback_text=feedback_data.feedback_text,
            wants_response=feedback_data.wants_response,
            created_at=datetime.utcnow(),
            status="open",
            priority="normal"
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        # Debug-Information
        print(f"[DEBUG] Feedback created with ID: {feedback.id}")
        print(f"[DEBUG] Feedback object: {feedback}")
        
        # Einfache Success-Response - ID kann None sein, macht nichts
        return AppFeedbackSuccessSchema(
            success=True,
            message="Feedback erfolgreich gesendet! Vielen Dank für dein Feedback.",
            feedback_id=feedback.id  # Kann None sein, ist OK
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"[ERROR] Exception in create_feedback: {str(e)}")
        print(f"[ERROR] Exception type: {type(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Erstellen des Feedbacks: {str(e)}"
        )

@router.get("/my", response_model=list[AppFeedbackResponseSchema])
async def get_my_feedback(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Alle Feedback-Einträge des aktuellen Nutzers abrufen.
    """
    try:
        user_uuid = UUID(current_user.id)
        
        statement = (
            select(AppFeedbackModel)
            .where(AppFeedbackModel.user_id == user_uuid)
            .order_by(AppFeedbackModel.created_at.desc())
        )
        result = await db.execute(statement)
        feedback_list = result.scalars().all()
        
        return [
            AppFeedbackResponseSchema(
                id=feedback.id,
                user_id=str(feedback.user_id),
                feedback_text=feedback.feedback_text,
                wants_response=feedback.wants_response,
                created_at=feedback.created_at,
                updated_at=feedback.updated_at,
                response_text=feedback.response_text,
                response_at=feedback.response_at,
                responded_by=feedback.responded_by,
                status=feedback.status,
                category=feedback.category,
                priority=feedback.priority
            )
            for feedback in feedback_list
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Feedbacks: {str(e)}"
        )

@router.get("/{feedback_id}", response_model=AppFeedbackResponseSchema)
async def get_feedback_by_id(
    feedback_id: int,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Einzelnes Feedback abrufen (nur eigenes Feedback).
    """
    try:
        user_uuid = UUID(current_user.id)
        
        # Feedback abrufen
        feedback_query = select(AppFeedbackModel).where(AppFeedbackModel.id == feedback_id)
        result = await db.execute(feedback_query)
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback nicht gefunden"
            )
        
        # Nur eigenes Feedback anzeigen
        if feedback.user_id != user_uuid:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Zugriff verweigert"
            )
        
        # Create response manually to ensure all fields are correct
        return AppFeedbackResponseSchema(
            id=feedback.id,
            user_id=str(feedback.user_id),
            feedback_text=feedback.feedback_text,
            wants_response=feedback.wants_response,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            response_text=feedback.response_text,
            response_at=feedback.response_at,
            responded_by=feedback.responded_by,
            status=feedback.status,
            category=feedback.category,
            priority=feedback.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen des Feedbacks: {str(e)}"
        )

# Admin/Support Endpoints (optional - für Support-Team)
@router.get("/admin/all", response_model=AppFeedbackListResponseSchema)
async def get_all_feedback_admin(
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    wants_response_only: bool = Query(False),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Alle Feedback-Einträge für Support-Team abrufen.
    TODO: Hier sollte eine Admin-Rolle geprüft werden.
    """
    try:
        # Basis-Query
        statement = select(AppFeedbackModel)
        
        # Filter anwenden
        if status_filter:
            statement = statement.where(AppFeedbackModel.status == status_filter)
        
        if wants_response_only:
            statement = statement.where(AppFeedbackModel.wants_response == True)
        
        # Total count für Pagination
        total_statement = statement
        total_result = await db.execute(total_statement)
        total = len(total_result.scalars().all())
        
        # Pagination anwenden
        statement = (
            statement
            .order_by(AppFeedbackModel.created_at.desc())
            .offset((page - 1) * size)
            .limit(size)
        )
        
        result = await db.execute(statement)
        feedback_list = result.scalars().all()
        
        return AppFeedbackListResponseSchema(
            feedbacks=[
                AppFeedbackResponseSchema(
                    id=feedback.id,
                    user_id=str(feedback.user_id),
                    feedback_text=feedback.feedback_text,
                    wants_response=feedback.wants_response,
                    created_at=feedback.created_at,
                    updated_at=feedback.updated_at,
                    response_text=feedback.response_text,
                    response_at=feedback.response_at,
                    responded_by=feedback.responded_by,
                    status=feedback.status,
                    category=feedback.category,
                    priority=feedback.priority
                )
                for feedback in feedback_list
            ],
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Abrufen aller Feedbacks: {str(e)}"
        )

@router.patch("/{feedback_id}", response_model=AppFeedbackResponseSchema)
async def update_feedback_admin(
    feedback_id: int,
    update_data: AppFeedbackUpdateSchema,
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Feedback aktualisieren (für Support-Team).
    TODO: Hier sollte eine Admin-Rolle geprüft werden.
    """
    try:
        # Feedback abrufen
        feedback_query = select(AppFeedbackModel).where(AppFeedbackModel.id == feedback_id)
        result = await db.execute(feedback_query)
        feedback = result.scalar_one_or_none()
        
        if not feedback:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Feedback nicht gefunden"
            )
        
        # Update-Daten anwenden
        update_dict = update_data.model_dump(exclude_unset=True)
        
        for key, value in update_dict.items():
            setattr(feedback, key, value)
        
        # Antwort-Timestamp setzen, wenn Antwort hinzugefügt wird
        if update_data.response_text and not feedback.response_at:
            feedback.response_at = datetime.utcnow()
        
        feedback.updated_at = datetime.utcnow()
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        # Create response manually to ensure all fields are correct
        return AppFeedbackResponseSchema(
            id=feedback.id,
            user_id=str(feedback.user_id),
            feedback_text=feedback.feedback_text,
            wants_response=feedback.wants_response,
            created_at=feedback.created_at,
            updated_at=feedback.updated_at,
            response_text=feedback.response_text,
            response_at=feedback.response_at,
            responded_by=feedback.responded_by,
            status=feedback.status,
            category=feedback.category,
            priority=feedback.priority
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Fehler beim Aktualisieren des Feedbacks: {str(e)}"
        ) 