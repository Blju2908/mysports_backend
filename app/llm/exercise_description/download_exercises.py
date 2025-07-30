"""
Download exercise descriptions from the database for enhancement.
"""
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import List, Optional
from sqlmodel import select

# Path setup
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

from app.models.exercise_description_model import ExerciseDescription
from app.db.session import get_background_session
import logging

logger = logging.getLogger(__name__)

async def download_all_exercise_descriptions() -> List[ExerciseDescription]:
    """
    Download all exercise descriptions from the database.
    
    Returns:
        List of ExerciseDescription objects from the database
    """
    try:
        async with get_background_session() as session:
            # Query all exercise descriptions
            stmt = select(ExerciseDescription)
            result = await session.exec(stmt)
            exercises = result.all()
            
            logger.info(f"📥 Downloaded {len(exercises)} exercise descriptions from database")
            return exercises
            
    except Exception as e:
        logger.error(f"❌ Error downloading exercise descriptions: {e}")
        raise

async def save_exercises_to_json(exercises: List[ExerciseDescription], output_path: Path) -> None:
    """
    Save exercise descriptions to JSON file for enhancement.
    
    Args:
        exercises: List of ExerciseDescription objects
        output_path: Path where to save the JSON file
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict format
        exercises_data = []
        for exercise in exercises:
            exercise_dict = exercise.model_dump()
            # Convert datetime objects to ISO format strings
            if exercise_dict.get('created_at'):
                exercise_dict['created_at'] = exercise_dict['created_at'].isoformat()
            if exercise_dict.get('updated_at'):
                exercise_dict['updated_at'] = exercise_dict['updated_at'].isoformat()
            exercises_data.append(exercise_dict)
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(exercises_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(exercises)} exercise descriptions to {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Error saving exercises to JSON: {e}")
        raise

async def download_and_save_exercises(output_file: Optional[str] = None) -> Path:
    """
    Download all exercise descriptions and save them to JSON file.
    
    Args:
        output_file: Optional custom output file path
        
    Returns:
        Path to the saved JSON file
    """
    # Default output path
    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"exercise_descriptions_download_{timestamp}.json"
    
    output_path = Path(__file__).parent / "output" / output_file
    
    logger.info("🚀 Starting download of exercise descriptions...")
    
    # Download from database
    exercises = await download_all_exercise_descriptions()
    
    if not exercises:
        logger.warning("⚠️ No exercise descriptions found in database")
        return output_path
    
    # Save to JSON
    await save_exercises_to_json(exercises, output_path)
    
    logger.info(f"✅ Download completed! File saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    asyncio.run(download_and_save_exercises())