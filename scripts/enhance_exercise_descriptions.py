#!/usr/bin/env python3
"""
Script to enhance exercise descriptions with new fields using LLM.
"""

# === CONFIGURATION ===
DEFAULT_INPUT_FILE = "exercise_descriptions_download_20250730_133605.json"
DEFAULT_OUTPUT_FILE = "enhanced_exercises.json"
DEFAULT_BATCH_SIZE = 5
DEFAULT_DELAY_BETWEEN_BATCHES = 1.0
DEFAULT_OUTPUT_DIR = "app/llm/exercise_description/output"
AUTO_SELECT_LATEST = True
CHECK_EXISTING_EXERCISES = True  # If True: skip existing exercises, If False: process all exercises

import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

# Load environment variables
import os
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.exercise_description.enhance_exercises_chain import (
    enhance_exercises_with_batching, 
    save_enhanced_exercises_to_json
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_exercise_json(input_path: Path) -> List[Dict[str, Any]]:
    """Load exercise descriptions from JSON file."""
    with open(input_path, 'r', encoding='utf-8') as f:
        exercises = json.load(f)
    
    if not isinstance(exercises, list):
        raise ValueError("JSON file must contain an array of exercise descriptions")
    
    logger.info(f"Loaded {len(exercises)} exercises from {input_path}")
    return exercises

def load_existing_enhanced_exercises(output_path: Path) -> List[Dict[str, Any]]:
    """Load existing enhanced exercises from output JSON file."""
    if not output_path.exists():
        return []
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            exercises = json.load(f)
        
        if isinstance(exercises, list):
            logger.info(f"Loaded {len(exercises)} existing enhanced exercises")
            return exercises
    except Exception as e:
        logger.warning(f"Error loading existing exercises: {e}")
    
    return []

def filter_new_exercises(input_exercises: List[Dict[str, Any]], existing_exercises: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter out exercises that already exist in the enhanced output."""
    if not existing_exercises:
        return input_exercises
    
    # Create set of existing English exercise names (normalized)
    existing_names = set()
    for exercise in existing_exercises:
        english_name = exercise.get('name_english', '').strip().lower()
        if english_name:
            existing_names.add(english_name)
    
    # Filter input exercises
    new_exercises = []
    for exercise in input_exercises:
        english_name = exercise.get('name_english', '').strip().lower()
        if not english_name or english_name not in existing_names:
            new_exercises.append(exercise)
        else:
            logger.info(f"Skipping existing exercise: {exercise.get('name_english', 'Unknown')}")
    
    logger.info(f"Filtered: {len(input_exercises)} input -> {len(new_exercises)} new exercises to process")
    return new_exercises

def get_input_file() -> str:
    """Get the input file based on configuration."""
    output_dir = BACKEND_DIR / DEFAULT_OUTPUT_DIR
    
    # Try default file first
    default_path = output_dir / DEFAULT_INPUT_FILE
    if default_path.exists():
        return str(default_path)
    
    # If auto-select is enabled, find latest download file
    if AUTO_SELECT_LATEST:
        download_files = list(output_dir.glob("*download*.json"))
        if download_files:
            latest_file = max(download_files, key=lambda f: f.stat().st_mtime)
            logger.info(f"Auto-selected latest download file: {latest_file.name}")
            return str(latest_file)
    
    return str(default_path)

async def main():
    """Main script entry point."""
    try:
        # Get input file
        input_file = get_input_file()
        input_path = Path(input_file)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Setup output path
        output_path = BACKEND_DIR / DEFAULT_OUTPUT_DIR / DEFAULT_OUTPUT_FILE
        
        # Load input exercises
        input_exercises = load_exercise_json(input_path)
        
        # Load existing enhanced exercises and filter if needed
        if CHECK_EXISTING_EXERCISES:
            existing_exercises = load_existing_enhanced_exercises(output_path)
            exercises_to_process = filter_new_exercises(input_exercises, existing_exercises)
        else:
            existing_exercises = []
            exercises_to_process = input_exercises
        
        logger.info(f"Configuration: Check existing={CHECK_EXISTING_EXERCISES}, Batch size={DEFAULT_BATCH_SIZE}")
        logger.info(f"Input: {len(input_exercises)}, Existing: {len(existing_exercises)}, To process: {len(exercises_to_process)}")
        
        # If no new exercises to process, we're done
        if not exercises_to_process:
            logger.info("No new exercises to process")
            return
        
        # Create save callback that merges with existing
        async def save_progress(enhanced_exercises):
            # Convert existing dicts to ExerciseSchema objects
            from app.llm.exercise_description.enhanced_exercise_schemas import ExerciseSchema
            existing_as_schemas = [ExerciseSchema(**ex) for ex in existing_exercises]
            all_exercises = existing_as_schemas + list(enhanced_exercises)
            await save_enhanced_exercises_to_json(all_exercises, output_path)
        
        # Run enhancement
        logger.info("Starting LLM enhancement...")
        start_time = datetime.now()
        
        enhanced_exercises = await enhance_exercises_with_batching(
            existing_exercises=exercises_to_process,
            batch_size=DEFAULT_BATCH_SIZE,
            delay_between_batches=DEFAULT_DELAY_BETWEEN_BATCHES,
            intermediate_save_callback=save_progress
        )
        
        # Final save
        from app.llm.exercise_description.enhanced_exercise_schemas import ExerciseSchema
        existing_as_schemas = [ExerciseSchema(**ex) for ex in existing_exercises]
        final_exercises = existing_as_schemas + list(enhanced_exercises)
        await save_enhanced_exercises_to_json(final_exercises, output_path)
        
        duration = datetime.now() - start_time
        logger.info(f"Enhancement completed in {duration.total_seconds():.2f}s")
        logger.info(f"Final result: {len(final_exercises)} total exercises saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())