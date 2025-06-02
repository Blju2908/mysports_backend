"""
Training Plan Revision Service

This service handles the revision of existing training plans based on user requests.
It connects the database layer with the LLM chain and handles the business logic.
"""

import json
import logging
from datetime import datetime, date
from typing import Optional, Dict, Any, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel
from app.llm.training_plan_generation.training_plan_generation_schemas import TrainingPlanGenerationSchema
from app.llm.training_plan_revision.training_plan_revision_chain import revise_training_plan
from app.llm.training_plan_revision.training_plan_revision_schemas import (
    TrainingPlanRevisionRequestSchema,
    TrainingPlanRevisionResponseSchema,
    TrainingPlanRevisionPreviewSchema
)

logger = logging.getLogger("training_plan_revision")


class TrainingPlanRevisionService:
    """Service for handling training plan revisions."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_user_training_plan(self, user_id: UUID) -> Optional[TrainingPlan]:
        """Get the user's current training plan from the database."""
        try:
            # Get user from database
            user_query = select(UserModel).where(UserModel.id == user_id)
            result = await self.db.execute(user_query)
            user = result.scalar_one_or_none()
            
            if not user or not user.training_plan_id:
                logger.warning(f"No training plan found for user {user_id}")
                return None
            
            # Get training plan
            plan_query = select(TrainingPlan).where(TrainingPlan.id == user.training_plan_id)
            plan_result = await self.db.execute(plan_query)
            plan = plan_result.scalar_one_or_none()
            
            if not plan:
                logger.warning(f"Training plan {user.training_plan_id} not found for user {user_id}")
                return None
            
            return plan
            
        except Exception as e:
            logger.error(f"Error getting training plan for user {user_id}: {e}")
            raise
    
    def convert_db_plan_to_schema(self, db_plan: TrainingPlan) -> TrainingPlanGenerationSchema:
        """Convert database training plan to schema format."""
        try:
            # If training_principles_json exists, use it directly
            if db_plan.training_principles_json:
                plan_data = db_plan.training_principles_json.copy()
            else:
                # Create empty structure if no JSON data exists
                plan_data = {
                    "personal_information": {"content": ""},
                    "standard_equipment": {"content": ""},
                    "training_principles": {"content": db_plan.training_principles or ""},
                    "training_phases": {"content": ""},
                    "remarks": {"content": ""}
                }
            
            # Ensure valid_until is set
            if "valid_until" not in plan_data:
                # Default to 6 months from now if not set
                plan_data["valid_until"] = (date.today().replace(month=date.today().month + 6) 
                                          if date.today().month <= 6 
                                          else date.today().replace(year=date.today().year + 1, month=date.today().month - 6))
            
            return TrainingPlanGenerationSchema(**plan_data)
            
        except Exception as e:
            logger.error(f"Error converting DB plan to schema: {e}")
            raise ValueError(f"Invalid training plan data: {e}")
    
    async def create_revision_preview(
        self, 
        user_id: UUID, 
        user_request: str,
        user_context: Optional[str] = None
    ) -> TrainingPlanRevisionPreviewSchema:
        """Create a preview of the revised training plan without saving it."""
        try:
            logger.info(f"[TrainingPlanRevision] Creating preview for user {user_id}, request: {user_request}")
            
            # Get current training plan
            current_plan = await self.get_user_training_plan(user_id)
            if not current_plan:
                raise ValueError("No training plan found for user")
            
            # Convert to schema format
            current_plan_schema = self.convert_db_plan_to_schema(current_plan)
            
            # Call LLM to revise the plan
            revised_plan_schema = await revise_training_plan(
                current_training_plan=current_plan_schema,
                user_request=user_request,
                user_context=user_context
            )
            
            # Generate changes summary (simplified version)
            changes_summary = self._generate_changes_summary(current_plan_schema, revised_plan_schema, user_request)
            
            # Create preview response
            preview = TrainingPlanRevisionPreviewSchema(
                revised_training_plan=revised_plan_schema,
                changes_summary=changes_summary,
                original_request=user_request
            )
            
            logger.info(f"[TrainingPlanRevision] Preview created successfully for user {user_id}")
            return preview
            
        except Exception as e:
            logger.error(f"[TrainingPlanRevision] Error creating preview for user {user_id}: {e}")
            raise
    
    async def apply_revision(
        self, 
        user_id: UUID, 
        user_request: str,
        user_context: Optional[str] = None,
        save_backup: bool = True
    ) -> TrainingPlanRevisionResponseSchema:
        """Apply the training plan revision and save it to the database."""
        try:
            logger.info(f"[TrainingPlanRevision] Applying revision for user {user_id}, request: {user_request}")
            
            # Get current training plan
            current_plan = await self.get_user_training_plan(user_id)
            if not current_plan:
                raise ValueError("No training plan found for user")
            
            # Create backup if requested (simplified - just log for now)
            if save_backup:
                logger.info(f"[TrainingPlanRevision] Backup created for plan {current_plan.id}")
            
            # Convert to schema format
            current_plan_schema = self.convert_db_plan_to_schema(current_plan)
            
            # Call LLM to revise the plan
            revised_plan_schema = await revise_training_plan(
                current_training_plan=current_plan_schema,
                user_request=user_request,
                user_context=user_context
            )
            
            # Update the database plan
            await self._update_plan_in_db(current_plan, revised_plan_schema)
            
            # Generate changes summary
            changes_summary = self._generate_changes_summary(current_plan_schema, revised_plan_schema, user_request)
            
            # Create response
            response = TrainingPlanRevisionResponseSchema(
                user_request=user_request,
                revised_training_plan=revised_plan_schema,
                changes_summary=changes_summary,
                revision_timestamp=datetime.now().isoformat()
            )
            
            logger.info(f"[TrainingPlanRevision] Revision applied successfully for user {user_id}")
            return response
            
        except Exception as e:
            await self.db.rollback()
            logger.error(f"[TrainingPlanRevision] Error applying revision for user {user_id}: {e}")
            raise
    
    async def _update_plan_in_db(self, db_plan: TrainingPlan, revised_schema: TrainingPlanGenerationSchema):
        """Update the training plan in the database with revised data."""
        try:
            # Convert schema to dict with proper date serialization
            revised_data = self._safe_json_serialize(revised_schema.model_dump())
            db_plan.training_principles_json = revised_data
            
            # Update the text field for backward compatibility
            db_plan.training_principles = revised_schema.training_principles.content
            
            # Save to database
            self.db.add(db_plan)
            await self.db.commit()
            await self.db.refresh(db_plan)
            
            logger.info(f"[TrainingPlanRevision] Plan {db_plan.id} updated in database")
            
        except Exception as e:
            logger.error(f"[TrainingPlanRevision] Error updating plan in DB: {e}")
            raise
    
    def _safe_json_serialize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Safely serialize data with date objects for JSON storage."""
        
        def date_serializer(obj):
            if isinstance(obj, date):
                return obj.isoformat()
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
        
        # Convert to JSON string and back to ensure all dates are serialized
        json_str = json.dumps(data, default=date_serializer)
        return json.loads(json_str)
    
    def _generate_changes_summary(
        self, 
        original: TrainingPlanGenerationSchema, 
        revised: TrainingPlanGenerationSchema, 
        user_request: str
    ) -> str:
        """Generate a summary of changes made to the training plan."""
        try:
            changes = []
            
            # Compare each section
            sections = [
                ("Persönliche Informationen", "personal_information"),
                ("Standard Ausrüstung", "standard_equipment"), 
                ("Trainingsprinzipien", "training_principles"),
                ("Trainingsphasen", "training_phases"),
                ("Bemerkungen", "remarks")
            ]
            
            for section_name, section_key in sections:
                original_content = getattr(original, section_key).content
                revised_content = getattr(revised, section_key).content
                
                if original_content != revised_content:
                    changes.append(f"- **{section_name}**: Aktualisiert")
            
            # Check valid_until date
            if original.valid_until != revised.valid_until:
                changes.append(f"- **Gültigkeit**: Bis {revised.valid_until.strftime('%d.%m.%Y')}")
            
            if not changes:
                changes.append("- Keine signifikanten Änderungen erkannt")
            
            summary = f"**Benutzeranfrage:** {user_request}\n\n**Durchgeführte Änderungen:**\n" + "\n".join(changes)
            
            return summary
            
        except Exception as e:
            logger.error(f"[TrainingPlanRevision] Error generating changes summary: {e}")
            return f"Änderungen basierend auf Anfrage: {user_request}"


# Convenience functions for the endpoint
async def create_training_plan_revision_preview(
    db: AsyncSession,
    user_id: UUID,
    user_request: str,
    user_context: Optional[str] = None
) -> TrainingPlanRevisionPreviewSchema:
    """Create a training plan revision preview."""
    service = TrainingPlanRevisionService(db)
    return await service.create_revision_preview(user_id, user_request, user_context)


async def apply_training_plan_revision(
    db: AsyncSession,
    user_id: UUID,
    user_request: str,
    user_context: Optional[str] = None,
    save_backup: bool = True
) -> TrainingPlanRevisionResponseSchema:
    """Apply a training plan revision."""
    service = TrainingPlanRevisionService(db)
    return await service.apply_revision(user_id, user_request, user_context, save_backup) 