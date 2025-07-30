"""
Upload enhanced exercise descriptions back to the database.
"""
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlmodel import select

# Path setup
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

from app.models.exercise_description_model import ExerciseDescription
from app.db.session import get_background_session
import logging

logger = logging.getLogger(__name__)

async def load_enhanced_exercises_from_json(json_path: Path) -> List[Dict[str, Any]]:
    """
    Load enhanced exercise descriptions from JSON file.
    
    Args:
        json_path: Path to the JSON file with enhanced exercises
        
    Returns:
        List of enhanced exercise descriptions as dicts
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            exercises_data = json.load(f)
        
        logger.info(f"📥 Loaded {len(exercises_data)} enhanced exercise descriptions from {json_path}")
        return exercises_data
        
    except Exception as e:
        logger.error(f"❌ Error loading enhanced exercises from JSON: {e}")
        raise

async def update_exercise_in_database(exercise_data: Dict[str, Any]) -> bool:
    """
    Update a single exercise description in the database.
    
    Args:
        exercise_data: Enhanced exercise description data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        async with get_background_session() as session:
            # Find existing exercise by name_german (primary key)
            name_german = exercise_data.get('name_german')
            if not name_german:
                logger.error("❌ Missing name_german in exercise data")
                return False
            
            stmt = select(ExerciseDescription).where(ExerciseDescription.name_german == name_german)
            result = await session.exec(stmt)
            existing_exercise = result.first()
            
            if existing_exercise:
                # Update existing exercise with new fields
                for key, value in exercise_data.items():
                    if hasattr(existing_exercise, key):
                        # Convert datetime strings back to datetime objects
                        if key in ['created_at', 'updated_at'] and isinstance(value, str):
                            try:
                                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                            except:
                                if key == 'updated_at':
                                    value = datetime.utcnow()
                                continue
                        
                        setattr(existing_exercise, key, value)
                
                # Always update the updated_at timestamp
                existing_exercise.updated_at = datetime.utcnow()
                
                session.add(existing_exercise)
                await session.commit()
                logger.info(f"✅ Updated exercise: {name_german}")
                return True
            else:
                logger.warning(f"⚠️ Exercise not found in database: {name_german}")
                return False
                
    except Exception as e:
        logger.error(f"❌ Error updating exercise {exercise_data.get('name_german', 'Unknown')}: {e}")
        return False

async def upload_enhanced_exercises_to_database(exercises_data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Upload all enhanced exercise descriptions to the database.
    
    Args:
        exercises_data: List of enhanced exercise descriptions
        
    Returns:
        Dict with counts of successful/failed updates
    """
    logger.info(f"🚀 Starting upload of {len(exercises_data)} enhanced exercises...")
    
    results = {
        'successful': 0,
        'failed': 0,
        'total': len(exercises_data)
    }
    
    for i, exercise_data in enumerate(exercises_data, 1):
        logger.info(f"📤 Uploading exercise {i}/{len(exercises_data)}: {exercise_data.get('name_german', 'Unknown')}")
        
        success = await update_exercise_in_database(exercise_data)
        if success:
            results['successful'] += 1
        else:
            results['failed'] += 1
        
        # Small delay to avoid overwhelming the database
        await asyncio.sleep(0.1)
    
    logger.info(f"✅ Upload completed! Successfully updated: {results['successful']}, Failed: {results['failed']}")
    return results

async def upload_enhanced_exercises_from_file(json_file: Optional[str] = None) -> Dict[str, int]:
    """
    Load enhanced exercises from JSON file and upload them to the database.
    
    Args:
        json_file: Optional path to JSON file. If None, looks for latest file in output folder
        
    Returns:
        Dict with upload results
    """
    try:
        # Determine input file
        if json_file is None:
            # Look for enhanced exercises files in output folder
            output_dir = Path(__file__).parent / "output"
            if not output_dir.exists():
                raise FileNotFoundError("Output directory not found. No enhanced exercises to upload.")
            
            # Find the most recent enhanced exercises file
            enhanced_files = list(output_dir.glob("*enhanced*.json"))
            if not enhanced_files:
                raise FileNotFoundError("No enhanced exercise files found in output directory.")
            
            # Get the most recent file
            json_file = max(enhanced_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"📁 Using latest enhanced exercises file: {json_file}")
        else:
            json_file = Path(json_file)
            if not json_file.is_absolute():
                json_file = Path(__file__).parent / "output" / json_file
        
        # Load and upload
        exercises_data = await load_enhanced_exercises_from_json(json_file)
        results = await upload_enhanced_exercises_to_database(exercises_data)
        
        logger.info(f"🎉 Upload process completed!")
        logger.info(f"📊 Results: {results}")
        
        return results
        
    except Exception as e:
        logger.error(f"❌ Error in upload process: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(upload_enhanced_exercises_from_file())