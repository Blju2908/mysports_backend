"""
Training Plan Revision Main

Main entry point for training plan revision functionality.
This module provides the high-level interface for revising training plans.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.training_plan_revision.training_plan_revision_service import (
    create_training_plan_revision_preview,
    apply_training_plan_revision
)
from app.llm.training_plan_revision.training_plan_revision_schemas import (
    TrainingPlanRevisionPreviewSchema,
    TrainingPlanRevisionResponseSchema
)

logger = logging.getLogger("training_plan_revision_main")


async def run_training_plan_revision_preview(
    user_id: UUID,
    user_request: str,
    db: AsyncSession,
    user_context: Optional[str] = None
) -> TrainingPlanRevisionPreviewSchema:
    """
    Generate a preview of a revised training plan without saving it.
    
    Args:
        user_id: UUID of the user requesting the revision
        user_request: The user's request for changes to their training plan
        db: Database session
        user_context: Optional additional context about the user's preferences
    
    Returns:
        TrainingPlanRevisionPreviewSchema: Preview of the revised training plan
    
    Raises:
        ValueError: If no training plan is found for the user
        Exception: For any other errors during the revision process
    """
    try:
        logger.info(f"[TrainingPlanRevisionMain] Starting preview generation for user {user_id}")
        logger.info(f"[TrainingPlanRevisionMain] User request: {user_request}")
        
        # Create the revision preview
        preview = await create_training_plan_revision_preview(
            db=db,
            user_id=user_id,
            user_request=user_request,
            user_context=user_context
        )
        
        logger.info(f"[TrainingPlanRevisionMain] Preview generated successfully for user {user_id}")
        logger.info(f"[TrainingPlanRevisionMain] Changes summary: {preview.changes_summary}")
        
        return preview
        
    except Exception as e:
        logger.error(f"[TrainingPlanRevisionMain] Error generating preview for user {user_id}: {e}")
        raise


async def run_training_plan_revision(
    user_id: UUID,
    user_request: str,
    db: AsyncSession,
    user_context: Optional[str] = None,
    save_backup: bool = True
) -> TrainingPlanRevisionResponseSchema:
    """
    Apply a training plan revision and save it to the database.
    
    Args:
        user_id: UUID of the user requesting the revision
        user_request: The user's request for changes to their training plan
        db: Database session
        user_context: Optional additional context about the user's preferences
        save_backup: Whether to save a backup of the original plan
    
    Returns:
        TrainingPlanRevisionResponseSchema: The completed revision with metadata
    
    Raises:
        ValueError: If no training plan is found for the user
        Exception: For any other errors during the revision process
    """
    try:
        logger.info(f"[TrainingPlanRevisionMain] Starting revision application for user {user_id}")
        logger.info(f"[TrainingPlanRevisionMain] User request: {user_request}")
        logger.info(f"[TrainingPlanRevisionMain] Save backup: {save_backup}")
        
        # Apply the revision
        response = await apply_training_plan_revision(
            db=db,
            user_id=user_id,
            user_request=user_request,
            user_context=user_context,
            save_backup=save_backup
        )
        
        logger.info(f"[TrainingPlanRevisionMain] Revision applied successfully for user {user_id}")
        logger.info(f"[TrainingPlanRevisionMain] Changes summary: {response.changes_summary}")
        
        return response
        
    except Exception as e:
        logger.error(f"[TrainingPlanRevisionMain] Error applying revision for user {user_id}: {e}")
        raise


# Development/Testing functions
async def test_training_plan_revision():
    """Test function for development purposes."""
    # This would typically be used for testing the revision functionality
    # with sample data during development
    
    print("Training Plan Revision Test")
    print("=" * 50)
    print("This is a placeholder for testing the training plan revision functionality.")
    print("In a real scenario, this would:")
    print("1. Connect to a test database")
    print("2. Load a sample training plan")
    print("3. Apply a test revision")
    print("4. Display the results")
    print("=" * 50)


if __name__ == "__main__":
    # Run test function if this module is executed directly
    asyncio.run(test_training_plan_revision()) 