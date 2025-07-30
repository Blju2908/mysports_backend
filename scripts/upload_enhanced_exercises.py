#!/usr/bin/env python3
"""
Script to upload enhanced exercise descriptions back to the database.

This script takes the enhanced exercise descriptions and updates the database records.
"""
import sys
import asyncio
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

from app.llm.exercise_description.upload_enhanced_exercises import upload_enhanced_exercises_from_file

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Main script entry point."""
    print("📤 Enhanced Exercise Descriptions Upload Script")
    print("=" * 50)
    print("This script will:")
    print("1. Load enhanced exercise descriptions from JSON file")
    print("2. Update existing records in the database with new fields")
    print("3. Provide upload statistics")
    print("=" * 50)
    
    try:
        # Check for enhanced files
        output_dir = BACKEND_DIR / "app" / "llm" / "exercise_description" / "output"
        enhanced_files = list(output_dir.glob("*enhanced*.json"))
        
        if not enhanced_files:
            print("❌ No enhanced exercise files found!")
            print(f"   Expected location: {output_dir}")
            print("   Please run the enhancement script first.")
            return
        
        # Show available files
        print("📁 Available enhanced exercise files:")
        for i, file in enumerate(enhanced_files, 1):
            print(f"   {i}. {file.name}")
        
        # File selection
        if len(enhanced_files) == 1:
            selected_file = enhanced_files[0]
            print(f"\n📄 Using: {selected_file.name}")
        else:
            print(f"\n📄 Using latest file: {enhanced_files[-1].name}")
            selected_file = enhanced_files[-1]
        
        # Ask for confirmation
        print(f"\n⚠️  This will update exercise descriptions in the database!")
        confirm = input("Proceed with upload? (y/N): ").strip().lower()
        if confirm not in ['y', 'yes']:
            print("Upload cancelled.")
            return
        
        # Perform upload
        print(f"\n🚀 Starting upload...")
        results = await upload_enhanced_exercises_from_file(str(selected_file))
        
        # Results summary
        print(f"\n📊 Upload Results:")
        print(f"   ✅ Successful updates: {results['successful']}")
        print(f"   ❌ Failed updates: {results['failed']}")
        print(f"   📊 Total processed: {results['total']}")
        
        success_rate = (results['successful'] / results['total']) * 100 if results['total'] > 0 else 0
        print(f"   📈 Success rate: {success_rate:.1f}%")
        
        if results['successful'] > 0:
            print(f"\n✅ Upload completed successfully!")
            print(f"📝 Note: You may need to update the database model to include new fields")
        else:
            print(f"\n❌ No exercises were successfully uploaded")
            
    except KeyboardInterrupt:
        print("\n⏹️ Upload cancelled by user")
    except Exception as e:
        logger.error(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())