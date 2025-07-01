#!/usr/bin/env python3
"""
Upload Script: Exercise Descriptions
Uploads exercise descriptions from JSON to database.
"""

import asyncio
import argparse
import sys
import os
import json
from datetime import datetime

# Add backend to path
backend_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.append(backend_path)

# Load environment variables
from dotenv import load_dotenv

# Determine which .env file to load
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(script_dir, '..', '..')

def load_environment(use_production=False):
    """Load appropriate environment file."""
    env_file = '.env.production' if use_production else '.env.development'
    env_path = os.path.join(backend_dir, env_file)
    
    if os.path.exists(env_path):
        load_dotenv(env_path)
        # Set APP_ENV for the config system
        os.environ['APP_ENV'] = 'production' if use_production else 'development'
        print(f"🔧 Environment geladen: {env_file}")
    else:
        print(f"❌ Environment-Datei nicht gefunden: {env_path}")
        return False
    return True

from sqlmodel import select, delete
from app.llm.utils.db_utils import create_db_session
from app.models.exercise_description_model import ExerciseDescription

async def upload_exercises(use_production: bool = False):
    """Upload exercises from JSON to database."""
    # Load environment first
    if not load_environment(use_production):
        return False
    
    # Use JSON file from same directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_file = os.path.join(script_dir, "exercise_descriptions.json")
    
    if not os.path.exists(json_file):
        print(f"❌ JSON-Datei nicht gefunden: {json_file}")
        return False
    
    # Load JSON
    with open(json_file, 'r', encoding='utf-8') as f:
        exercises_data = json.load(f)
    
    print(f"📋 {len(exercises_data)} Übungen geladen")
    
    async for session in create_db_session(use_production=use_production):
        # Clear existing data
        await session.execute(delete(ExerciseDescription))
        
        # Insert new data
        for exercise_data in exercises_data:
            exercise = ExerciseDescription(
                name_german=exercise_data['name_german'],
                name_english=exercise_data['name_english'], 
                description_german=exercise_data['description_german'],
                difficulty_level=exercise_data['difficulty_level'],
                primary_movement_pattern=exercise_data['primary_movement_pattern'],
                is_unilateral=exercise_data['is_unilateral'],
                equipment_options=exercise_data['equipment_options'],
                target_muscle_groups=exercise_data['target_muscle_groups'],
                execution_steps=exercise_data['execution_steps'],
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(exercise)
        
        await session.commit()
        
        # Quick verification
        result = await session.execute(select(ExerciseDescription))
        count = len(result.scalars().all())
        print(f"✅ {count} Übungen hochgeladen")
        
        return True


async def main():
    parser = argparse.ArgumentParser(description='Upload Exercise Descriptions')
    parser.add_argument('--production', action='store_true', help='Use production database')
    args = parser.parse_args()
    
    if args.production:
        confirm = input("⚠️  Produktionsdatenbank? (ja/nein): ")
        if confirm.lower() not in ['ja', 'yes', 'y']:
            print("Abgebrochen.")
            return
    
    success = await upload_exercises(use_production=args.production)
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 