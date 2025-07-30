#!/usr/bin/env python3
"""
Script to download exercise descriptions from the database for backup or analysis.

This script downloads all exercise descriptions and saves them to a JSON file.
"""
import sys
import asyncio
import json
import logging
from pathlib import Path

# Add backend directory to path
BACKEND_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BACKEND_DIR))

# Load environment variables BEFORE importing modules that need them
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.exercise_description.download_exercises import download_and_save_exercises

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main script entry point."""
    print("📥 Exercise Descriptions Download Script")
    print("=" * 50)
    print("This script will:")
    print("1. Connect to the database")
    print("2. Download all exercise descriptions")
    print("3. Save them to a timestamped JSON file")
    print("=" * 50)
    
    try:
        # Ask for confirmation
        confirm = input("Start download? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Download cancelled.")
            return
        
        # Perform download
        print("\n🚀 Starting download...")
        output_path = await download_and_save_exercises()
        
        if output_path and output_path.exists():
            print("\n✅ Download completed!")
            print(f"📁 Exercise descriptions saved to: {output_path}")
            
            # Show file info
            file_size = output_path.stat().st_size / 1024  # KB
            print(f"📊 File size: {file_size:.1f} KB")
            
            with open(output_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                print(f"📋 Total exercises: {len(data)}")
        else:
            print("❌ Download failed or no exercises found")
            
    except KeyboardInterrupt:
        print("\n⏹️ Download cancelled by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())