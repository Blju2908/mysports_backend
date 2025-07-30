#!/usr/bin/env python3
"""
Script to enhance exercise descriptions with new fields using LLM.

This script takes a JSON file with exercise descriptions, processes them through
OpenAI LLM to add new fields, and saves the enhanced results to another JSON file.

Configuration is now fixed in the script - no command line arguments needed.

Usage:
    python scripts/enhance_exercise_descriptions.py
    python scripts/enhance_exercise_descriptions.py --interactive
"""

# === FIXED CONFIGURATION ===
DEFAULT_INPUT_FILE = "exercise_descriptions_download_20250730_133605.json"
DEFAULT_OUTPUT_FILE = "enhanced_exercises.json"  # Fixed output file for all enhancements
DEFAULT_BATCH_SIZE = 5  # Smaller batches for complex enhancement
DEFAULT_DELAY_BETWEEN_BATCHES = 1.0  # Longer delay for stability
DEFAULT_OUTPUT_DIR = "app/llm/exercise_description/output"
AUTO_SELECT_LATEST = True  # Automatically use latest download file if default not found
# Toggle options for duplicate handling
CHECK_EXISTING_EXERCISES = True  # Check if English exercise name already exists in output
OVERWRITE_EXISTING = False  # If True, overwrite existing exercises; if False, skip LLM call
import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

# Load environment variables BEFORE importing modules that need them
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.exercise_description.enhance_exercises_chain import (
    enhance_exercises_with_batching, 
    save_enhanced_exercises_to_json
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_exercise_json(input_path: Path) -> List[Dict[str, Any]]:
    """Load exercise descriptions from JSON file."""
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            exercises = json.load(f)
        
        if not isinstance(exercises, list):
            raise ValueError("JSON file must contain an array of exercise descriptions")
        
        logger.info(f"📥 Loaded {len(exercises)} exercises from {input_path}")
        return exercises
        
    except Exception as e:
        logger.error(f"❌ Error loading exercises from {input_path}: {e}")
        raise

def load_existing_enhanced_exercises(output_path: Path) -> List[Dict[str, Any]]:
    """Load existing enhanced exercises from output JSON file."""
    try:
        if not output_path.exists():
            logger.info(f"📄 No existing output file found at {output_path}")
            return []
        
        with open(output_path, 'r', encoding='utf-8') as f:
            exercises = json.load(f)
        
        if not isinstance(exercises, list):
            logger.warning(f"⚠️ Existing output file format invalid, treating as empty")
            return []
        
        logger.info(f"📥 Loaded {len(exercises)} existing enhanced exercises from {output_path}")
        return exercises
        
    except Exception as e:
        logger.warning(f"⚠️ Error loading existing exercises from {output_path}: {e}")
        return []

def filter_exercises_by_existing(
    input_exercises: List[Dict[str, Any]], 
    existing_exercises: List[Dict[str, Any]], 
    check_existing: bool, 
    overwrite_existing: bool
) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter input exercises based on existing enhanced exercises.
    
    Args:
        input_exercises: New exercises to potentially enhance
        existing_exercises: Already enhanced exercises 
        check_existing: Whether to check for duplicates
        overwrite_existing: Whether to overwrite or skip existing exercises
        
    Returns:
        Tuple of (exercises_to_process, exercises_to_keep_from_existing)
    """
    if not check_existing:
        logger.info("🔄 Duplicate checking disabled, processing all exercises")
        return input_exercises, existing_exercises
    
    # Create lookup set of existing English exercise names
    existing_english_names = set()
    for exercise in existing_exercises:
        english_name = exercise.get('english_name', '').strip().lower()
        if english_name:
            existing_english_names.add(english_name)
    
    exercises_to_process = []
    exercises_to_skip = []
    
    for exercise in input_exercises:
        english_name = exercise.get('english_name', '').strip().lower()
        
        if english_name and english_name in existing_english_names:
            if overwrite_existing:
                logger.info(f"🔄 Will overwrite existing exercise: {exercise.get('english_name', 'Unknown')}")
                exercises_to_process.append(exercise)
            else:
                logger.info(f"⏭️ Skipping existing exercise: {exercise.get('english_name', 'Unknown')}")
                exercises_to_skip.append(exercise)
        else:
            exercises_to_process.append(exercise)
    
    # Determine which existing exercises to keep
    if overwrite_existing:
        # Remove existing exercises that will be overwritten
        new_english_names = {ex.get('english_name', '').strip().lower() for ex in exercises_to_process}
        exercises_to_keep = [
            ex for ex in existing_exercises 
            if ex.get('english_name', '').strip().lower() not in new_english_names
        ]
    else:
        # Keep all existing exercises
        exercises_to_keep = existing_exercises
    
    logger.info(f"📊 Filtering results:")
    logger.info(f"   🆕 Exercises to process: {len(exercises_to_process)}")
    logger.info(f"   ⏭️ Exercises to skip: {len(exercises_to_skip)}")
    logger.info(f"   📚 Existing exercises to keep: {len(exercises_to_keep)}")
    
    return exercises_to_process, exercises_to_keep

async def enhance_exercises_from_json(
    input_file: str,
    output_file: Optional[str] = None,
    batch_size: int = 5,
    delay_between_batches: float = 2.0,
    check_existing: bool = CHECK_EXISTING_EXERCISES,
    overwrite_existing: bool = OVERWRITE_EXISTING
) -> Path:
    """
    Enhance exercises from input JSON file and save to output JSON file.
    
    Args:
        input_file: Path to input JSON file with exercise descriptions
        output_file: Optional path to output file (auto-generated if None)
        batch_size: Number of exercises per LLM batch
        delay_between_batches: Delay between batches in seconds
        check_existing: Whether to check for existing exercises in output
        overwrite_existing: Whether to overwrite existing exercises or skip them
        
    Returns:
        Path to the output file
    """
    # Resolve input path
    input_path = Path(input_file)
    if not input_path.is_absolute():
        # Try relative to current directory first
        if input_path.exists():
            input_path = input_path.resolve()
        else:
            # Try relative to exercise_description output folder
            input_path = BACKEND_DIR / "app" / "llm" / "exercise_description" / "output" / input_file
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load input exercises
    input_exercises = load_exercise_json(input_path)
    
    if not input_exercises:
        raise ValueError("No exercises found in input file")
    
    # Determine output path - use DEFAULT_OUTPUT_FILE if none specified
    if output_file is None:
        output_filename = DEFAULT_OUTPUT_FILE
        output_path = BACKEND_DIR / "app" / "llm" / "exercise_description" / "output" / output_filename
    else:
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = BACKEND_DIR / "app" / "llm" / "exercise_description" / "output" / output_file
    
    # Load existing enhanced exercises
    existing_enhanced_exercises = load_existing_enhanced_exercises(output_path)
    
    # Filter exercises based on existing ones
    exercises_to_process, existing_exercises_to_keep = filter_exercises_by_existing(
        input_exercises=input_exercises,
        existing_exercises=existing_enhanced_exercises,
        check_existing=check_existing,
        overwrite_existing=overwrite_existing
    )
    
    logger.info(f"🎯 Enhancement Configuration:")
    logger.info(f"   📁 Input file: {input_path}")
    logger.info(f"   📤 Output file: {output_path}")
    logger.info(f"   📊 Total input exercises: {len(input_exercises)}")
    logger.info(f"   🆕 Exercises to process: {len(exercises_to_process)}")
    logger.info(f"   📚 Existing exercises to keep: {len(existing_exercises_to_keep)}")
    logger.info(f"   🔧 Batch size: {batch_size}")
    logger.info(f"   ⏱️ Delay between batches: {delay_between_batches}s")
    logger.info(f"   🔍 Check existing: {check_existing}")
    logger.info(f"   🔄 Overwrite existing: {overwrite_existing}")
    
    # If no exercises to process, just save existing ones
    if not exercises_to_process:
        logger.info("ℹ️ No new exercises to process, keeping existing enhanced exercises")
        if existing_exercises_to_keep:
            # Convert to ExerciseSchema objects if needed
            from app.llm.exercise_description.enhanced_exercise_schemas import ExerciseSchema
            enhanced_exercises = [
                ExerciseSchema(**ex) if isinstance(ex, dict) else ex 
                for ex in existing_exercises_to_keep
            ]
            await save_enhanced_exercises_to_json(enhanced_exercises, output_path)
        
        logger.info(f"✅ Completed with {len(existing_exercises_to_keep)} existing exercises")
        return output_path
    
    # Create intermediate save callback that merges with existing exercises
    async def save_progress(current_enhanced_exercises):
        """Save current progress merged with existing exercises"""
        # Merge current enhanced exercises with existing ones to keep
        all_exercises = list(existing_exercises_to_keep) + list(current_enhanced_exercises)
        await save_enhanced_exercises_to_json(all_exercises, output_path)
    
    # Run enhancement on filtered exercises
    logger.info("🤖 Starting LLM enhancement...")
    start_time = datetime.now()
    
    enhanced_exercises = await enhance_exercises_with_batching(
        existing_exercises=exercises_to_process,
        batch_size=batch_size,
        delay_between_batches=delay_between_batches,
        intermediate_save_callback=save_progress
    )
    
    # Merge with existing exercises that we want to keep
    final_exercises = list(existing_exercises_to_keep) + list(enhanced_exercises)
    
    # Final save (in case the last batch wasn't saved via callback)
    await save_enhanced_exercises_to_json(final_exercises, output_path)
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info(f"✅ ENHANCEMENT COMPLETED")
    logger.info(f"{'='*60}")
    logger.info(f"📊 Total input exercises: {len(input_exercises)}")
    logger.info(f"🆕 Exercises processed: {len(exercises_to_process)}")
    logger.info(f"🤖 Exercises enhanced: {len(enhanced_exercises)}")
    logger.info(f"📚 Existing exercises kept: {len(existing_exercises_to_keep)}")
    logger.info(f"📋 Total final exercises: {len(final_exercises)}")
    logger.info(f"⏱️ Processing time: {duration.total_seconds():.2f} seconds")
    logger.info(f"💾 Output saved to: {output_path}")
    logger.info(f"{'='*60}")
    
    return output_path

def print_usage():
    """Print usage information."""
    print("Exercise Description Enhancement Script")
    print("Enhances exercise descriptions with LLM-generated metadata.")
    print()
    print("Usage:")
    print("  python scripts/enhance_exercise_descriptions.py")
    print("  python scripts/enhance_exercise_descriptions.py --interactive")
    print()
    print("Configuration:")
    print(f"  Input file: {DEFAULT_INPUT_FILE}")
    print(f"  Batch size: {DEFAULT_BATCH_SIZE}")
    print(f"  Delay: {DEFAULT_DELAY_BETWEEN_BATCHES}s")
    print(f"  Auto-select latest: {AUTO_SELECT_LATEST}")
    print(f"  Check existing exercises: {CHECK_EXISTING_EXERCISES}")
    print(f"  Overwrite existing: {OVERWRITE_EXISTING}")

def find_available_exercise_files() -> List[Path]:
    """Find available exercise description files."""
    output_dir = BACKEND_DIR / "app" / "llm" / "exercise_description" / "output"
    if not output_dir.exists():
        return []
    
    # Find download files (not enhanced files)
    download_files = list(output_dir.glob("*download*.json"))
    return sorted(download_files, key=lambda f: f.stat().st_mtime, reverse=True)

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
            logger.info(f"📁 Auto-selected latest download file: {latest_file.name}")
            return str(latest_file)
    
    # Fallback to default (will cause error if not found)
    return str(default_path)

async def main():
    """Main script entry point with fixed configuration."""
    try:
        args = sys.argv[1:]
        
        if args and (args[0] == "--help" or args[0] == "-h"):
            print_usage()
            return
        
        # Use fixed configuration
        input_file = get_input_file()
        batch_size = DEFAULT_BATCH_SIZE
        delay = DEFAULT_DELAY_BETWEEN_BATCHES
        
        logger.info("Using fixed configuration:")
        logger.info(f"  Batch size: {batch_size}, Delay: {delay}s")
        logger.info(f"  Check existing: {CHECK_EXISTING_EXERCISES}, Overwrite: {OVERWRITE_EXISTING}")
        
        # Run enhancement with fixed configuration
        output_path = await enhance_exercises_from_json(
            input_file=input_file,
            output_file=None,
            batch_size=batch_size,
            delay_between_batches=delay,
            check_existing=CHECK_EXISTING_EXERCISES,
            overwrite_existing=OVERWRITE_EXISTING
        )
        
        print(f"\nEnhancement completed!")
        print(f"Output: {output_path}")
        
    except KeyboardInterrupt:
        print("\nEnhancement cancelled by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())