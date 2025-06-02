# backend/app/routers/training_plan.py - SIMPLIFIED VERSION
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlmodel import Session, select
from app.models.training_plan_model import TrainingPlan
from app.core.auth import get_current_user, User
from app.db.session import get_session
from app.schemas.training_plan_schema import TrainingPlanSchema, APIResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
import logging
from app.models.user_model import UserModel
from typing import Dict, Any
import json
from datetime import date
from app.llm.training_plan_generation.training_plan_generation_service import run_training_plan_generation

router = APIRouter(tags=["training-plan"])
logger = logging.getLogger("training_plan")

# 🔧 HELPER FUNCTIONS - Reduce duplication
async def get_or_create_user(db: AsyncSession, user_id: UUID) -> UserModel:
    """Get user from DB or create if doesn't exist"""
    user_query = select(UserModel).where(UserModel.id == user_id)
    result = await db.execute(user_query)
    user = result.scalar_one_or_none()
    
    if not user:
        user = UserModel(id=user_id)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    return user

async def get_or_create_training_plan(db: AsyncSession, user: UserModel) -> TrainingPlan:
    """Get user's training plan or create empty one"""
    if user.training_plan_id:
        # Try to get existing plan
        plan_query = select(TrainingPlan).where(TrainingPlan.id == user.training_plan_id)
        plan_result = await db.execute(plan_query)
        plan = plan_result.scalar_one_or_none()
        
        if plan:
            return plan
    
    # Create new empty plan with defaults
    new_plan = TrainingPlan(
        equipment="",
        session_duration=45,
        training_frequency=3,
        fitness_level=3,
        experience_level=3,
        include_cardio=True
    )
    db.add(new_plan)
    await db.commit()
    await db.refresh(new_plan)
    
    # Link user to plan
    user.training_plan_id = new_plan.id
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    return new_plan

def safe_json_serialize(data: Dict[str, Any]) -> Dict[str, Any]:
    """Safely serialize data with date objects"""
    def date_serializer(obj):
        if isinstance(obj, date):
            return obj.isoformat()
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
    
    # Convert to JSON string and back to ensure all dates are serialized
    json_str = json.dumps(data, default=date_serializer)
    return json.loads(json_str)

# 🎯 SIMPLIFIED ENDPOINTS
@router.get("/mine", response_model=Dict[str, Any])
async def get_my_training_plan(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Get current user's training plan"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Get or create user
        user = await get_or_create_user(db, user_uuid)
        
        # Get or create training plan
        plan = await get_or_create_training_plan(db, user)
        
        # Convert to frontend format
        plan_dict = plan.model_dump()
        schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[Get] Successfully retrieved plan for user {user_uuid}")
        return schema.to_frontend_format()
        
    except Exception as e:
        logger.error(f"[Get] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Laden des Trainingsplans: {str(e)}"
        )

@router.put("/mine", response_model=Dict[str, Any])
async def update_my_training_plan(
    plan_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update current user's training plan"""
    try:
        logger.info(f"[Update] Received data: {plan_data}")
        
        user_uuid = UUID(current_user.id)
        
        # Get or create user
        user = await get_or_create_user(db, user_uuid)
        
        # Get or create training plan
        plan = await get_or_create_training_plan(db, user)
        
        # Convert from frontend format and validate
        schema = TrainingPlanSchema.from_frontend_format(plan_data)
        
        # Update plan with validated data
        update_data = schema.model_dump(exclude_unset=True, exclude={"id"})
        for key, value in update_data.items():
            if key != "id":  # Never update ID
                setattr(plan, key, value)
        
        # Save changes
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Return updated plan
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[Update] Successfully updated plan {plan.id} for user {user_uuid}")
        return response_schema.to_frontend_format()
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[Update] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Aktualisieren des Trainingsplans: {str(e)}"
        )

@router.post("/generate-training-principles", response_model=Dict[str, Any])
async def generate_training_principles(
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Generate training principles for current user's plan using the new simplified structure"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Get user and plan
        user = await get_or_create_user(db, user_uuid)
        plan = await get_or_create_training_plan(db, user)
        
        # Remove the column training_principles_json from the plan
        plan.training_principles_json = None
        plan.training_principles = ""
        
        # Generate new training principles using the simplified service
        # This automatically saves the new principles to the database
        generated_plan = await run_training_plan_generation(user_uuid, db)
        
        # Reload the updated plan from database to get the complete saved data
        await db.refresh(plan)
        
        # Convert to schema and return in frontend format
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        result = response_schema.to_frontend_format()
        
        logger.info(f"[GeneratePrinciples] Successfully generated and saved principles for user {user_uuid}")
        return result
        
    except Exception as e:
        logger.error(f"[GeneratePrinciples] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Generieren der Trainingsprinzipien: {str(e)}"
        )

@router.post("/update-training-principles", response_model=Dict[str, Any])
async def update_training_principles(
    principles_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update training principles for current user's plan - supports both old and new structure"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Get user and plan
        user = await get_or_create_user(db, user_uuid)
        plan = await get_or_create_training_plan(db, user)
        
        # Safely serialize the principles data
        serialized_data = safe_json_serialize(principles_data)
        
        # Update training principles
        plan.training_principles_json = serialized_data
        
        # Update text version - handle both old and new structure
        if "training_principles_text" in principles_data:
            plan.training_principles = principles_data["training_principles_text"]
        elif "training_principles" in principles_data and isinstance(principles_data["training_principles"], dict):
            # New structure: use the content field
            plan.training_principles = principles_data["training_principles"].get("content", "")
        
        # Save changes
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Return updated plan
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[UpdatePrinciples] Successfully updated principles for user {user_uuid}")
        return response_schema.to_frontend_format()
        
    except Exception as e:
        await db.rollback()
        logger.error(f"[UpdatePrinciples] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Aktualisieren der Trainingsprinzipien: {str(e)}"
        )

@router.patch("/update-category", response_model=Dict[str, Any])
async def update_training_principles_category(
    category_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update a specific category in the training principles"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Validate required fields
        if "category" not in category_data or "content" not in category_data:
            raise HTTPException(
                status_code=400,
                detail="Fehlende Felder: 'category' und 'content' sind erforderlich"
            )
        
        category = category_data["category"]
        content = category_data["content"]
        
        logger.info(f"[UpdateCategory] Updating category '{category}' for user {user_uuid}")
        
        # Get user and plan
        user = await get_or_create_user(db, user_uuid)
        plan = await get_or_create_training_plan(db, user)
        
        # Initialize training_principles_json if not exists
        if not plan.training_principles_json:
            plan.training_principles_json = {}
        
        # Update the specific category
        current_principles = plan.training_principles_json.copy()
        current_principles[category] = {"content": content}
        
        # Safely serialize and update
        serialized_data = safe_json_serialize(current_principles)
        plan.training_principles_json = serialized_data
        
        # Update the text version if it's the main training_principles category
        if category == "training_principles":
            plan.training_principles = content
        
        # Save changes
        db.add(plan)
        await db.commit()
        await db.refresh(plan)
        
        # Return updated plan
        plan_dict = plan.model_dump()
        response_schema = TrainingPlanSchema(**plan_dict)
        
        logger.info(f"[UpdateCategory] Successfully updated category '{category}' for user {user_uuid}")
        return response_schema.to_frontend_format()
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[UpdateCategory] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Aktualisieren der Kategorie: {str(e)}"
        )

@router.post("/chat-revision-preview", response_model=Dict[str, Any])
async def create_training_plan_chat_revision_preview(
    chat_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Create a preview of training plan revision based on user chat input"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Validate required fields
        if "user_request" not in chat_data:
            raise HTTPException(
                status_code=400,
                detail="Fehlende Felder: 'user_request' ist erforderlich"
            )
        
        user_request = chat_data["user_request"]
        user_context = chat_data.get("user_context")
        
        logger.info(f"[ChatRevisionPreview] Processing preview request for user {user_uuid}: {user_request}")
        
        # Import the training plan revision service
        from app.llm.training_plan_revision.revise_training_plan_main import run_training_plan_revision_preview
        
        # Create revision preview using LLM
        preview = await run_training_plan_revision_preview(
            user_id=user_uuid,
            user_request=user_request,
            db=db,
            user_context=user_context
        )
        
        # Convert to frontend format
        result = {
            "revised_training_plan": preview.revised_training_plan.model_dump(),
            "changes_summary": preview.changes_summary,
            "original_request": preview.original_request
        }
        
        logger.info(f"[ChatRevisionPreview] Successfully created preview for user {user_uuid}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"[ChatRevisionPreview] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Erstellen der Vorschau: {str(e)}"
        )


@router.post("/update-via-chat", response_model=Dict[str, Any])
async def update_training_plan_via_chat(
    chat_data: Dict[str, Any] = Body(...),
    db: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Update training plan based on user chat input using LLM"""
    try:
        user_uuid = UUID(current_user.id)
        
        # Validate required fields
        if "user_request" not in chat_data:
            raise HTTPException(
                status_code=400,
                detail="Fehlende Felder: 'user_request' ist erforderlich"
            )
        
        user_request = chat_data["user_request"]
        user_context = chat_data.get("user_context")
        save_backup = chat_data.get("save_backup", True)
        
        logger.info(f"[UpdateViaChat] Processing LLM request for user {user_uuid}: {user_request}")
        
        # Import the training plan revision service
        from app.llm.training_plan_revision.revise_training_plan_main import run_training_plan_revision
        
        # Apply revision using LLM
        response = await run_training_plan_revision(
            user_id=user_uuid,
            user_request=user_request,
            db=db,
            user_context=user_context,
            save_backup=save_backup
        )
        
        # Convert to frontend format
        result = {
            "training_principles": response.revised_training_plan.training_principles.content,
            "training_principles_json": response.revised_training_plan.model_dump(),
            "changes_summary": response.changes_summary,
            "revision_timestamp": response.revision_timestamp
        }
        
        logger.info(f"[UpdateViaChat] Successfully updated plan via LLM chat for user {user_uuid}")
        return result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"[UpdateViaChat] Error for user {current_user.id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Fehler beim Aktualisieren über Chat: {str(e)}"
        )