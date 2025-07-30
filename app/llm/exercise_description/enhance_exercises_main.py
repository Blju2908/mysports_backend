"""
Main script for enhancing exercise descriptions with new fields.
This script downloads existing exercises, enhances them with LLM, and saves the results.
"""
import sys
from pathlib import Path
import asyncio
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

# Path setup
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.exercise_description.download_exercises import download_and_save_exercises
from app.llm.exercise_description.enhance_exercises_chain import (
    enhance_exercises_with_batching, 
    save_enhanced_exercises_to_json
)
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def enhance_all_exercises(
    batch_size: int = 5,
    delay_between_batches: float = 3.0,
    custom_input_file: Optional[str] = None
) -> Path:
    """
    Complete workflow: Download exercises, enhance them, and save results.
    
    Args:
        batch_size: Number of exercises per batch for LLM processing
        delay_between_batches: Pause between batches in seconds  
        custom_input_file: Optional custom input file instead of downloading from DB
        
    Returns:
        Path to the saved enhanced exercises JSON file
    """
    logger.info("🏋️ Starting Exercise Enhancement Workflow")
    logger.info("=" * 60)
    
    start_time = datetime.now()
    
    try:
        # Step 1: Get existing exercises
        if custom_input_file:
            logger.info(f"📁 Using custom input file: {custom_input_file}")
            input_path = Path(custom_input_file)
            if not input_path.is_absolute():
                input_path = Path(__file__).parent / "output" / custom_input_file
            
            with open(input_path, 'r', encoding='utf-8') as f:
                existing_exercises = json.load(f)
            logger.info(f"📥 Loaded {len(existing_exercises)} exercises from file")
        else:
            logger.info("📥 Downloading exercises from database...")
            download_path = await download_and_save_exercises()
            
            with open(download_path, 'r', encoding='utf-8') as f:
                existing_exercises = json.load(f)
        
        if not existing_exercises:
            logger.warning("⚠️ No exercises found to enhance")
            return Path()
        
        logger.info(f"📊 Found {len(existing_exercises)} exercises to enhance")
        
        # Step 2: Enhance exercises with LLM
        logger.info(f"🤖 Starting LLM enhancement (batch size: {batch_size})...")
        enhanced_exercises = await enhance_exercises_with_batching(
            existing_exercises=existing_exercises,
            batch_size=batch_size,
            delay_between_batches=delay_between_batches
        )
        
        if not enhanced_exercises:
            logger.error("❌ No exercises were successfully enhanced")
            return Path()
        
        # Step 3: Save enhanced exercises
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"exercise_descriptions_enhanced_{timestamp}.json"
        output_path = Path(__file__).parent / "output" / output_filename
        
        await save_enhanced_exercises_to_json(enhanced_exercises, output_path)
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        # Results summary
        logger.info(f"\n{'='*60}")
        logger.info(f"✅ EXERCISE ENHANCEMENT COMPLETED")
        logger.info(f"{'='*60}")
        logger.info(f"📊 Original exercises: {len(existing_exercises)}")
        logger.info(f"🤖 Enhanced exercises: {len(enhanced_exercises)}")
        logger.info(f"⏱️ Total processing time: {duration.total_seconds():.2f} seconds")
        logger.info(f"💾 Enhanced exercises saved to: {output_path}")
        logger.info(f"{'='*60}")
        
        # Show example of enhanced exercise
        if enhanced_exercises:
            first_exercise = enhanced_exercises[0]
            logger.info(f"\n📋 Example Enhanced Exercise: {first_exercise.name_german}")
            logger.info(f"🎯 Exercise Type: {first_exercise.exercise_type}")
            logger.info(f"💪 Primary Muscles: {', '.join(first_exercise.primary_muscle_groups)}")
            logger.info(f"🔧 Movement Category: {first_exercise.movement_category}")
            logger.info(f"⚡ Metabolic Demand: {first_exercise.metabolic_demand}")
        
        return output_path
        
    except Exception as e:
        logger.error(f"❌ Error in enhancement workflow: {e}")
        import traceback
        traceback.print_exc()
        raise

async def main():
    """Main function with user interaction for configuration."""
    logger.info("🏋️ Exercise Description Enhancement System")
    logger.info("=" * 50)
    
    try:
        # Configuration
        print("\n📋 Enhancement Configuration:")
        print("1. Batch size (exercises per LLM call): Recommended 3-5 for complex enhancement")
        print("2. Delay between batches: Recommended 3-5 seconds")
        print("3. Input source: Database download (default) or custom JSON file")
        
        # Get user input or use defaults
        batch_size = 5
        delay = 3.0
        custom_file = None
        
        # Interactive configuration (commented out for automatic mode)
        # batch_size = int(input("Enter batch size (default 5): ") or "5")
        # delay = float(input("Enter delay between batches in seconds (default 3.0): ") or "3.0")
        # custom_file = input("Enter custom input file name (or press Enter to download from DB): ").strip() or None
        
        logger.info(f"🔧 Configuration: batch_size={batch_size}, delay={delay}s")
        if custom_file:
            logger.info(f"📁 Using custom input file: {custom_file}")
        else:
            logger.info("📥 Will download exercises from database")
        
        # Start enhancement process
        output_path = await enhance_all_exercises(
            batch_size=batch_size,
            delay_between_batches=delay,
            custom_input_file=custom_file
        )
        
        if output_path and output_path.exists():
            logger.info(f"\n🎉 Enhancement completed successfully!")
            logger.info(f"📁 Enhanced exercises file: {output_path}")
            logger.info(f"📤 Next step: Run upload script to save enhanced exercises to database")
        else:
            logger.error("❌ Enhancement failed or no output generated")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())