"""
User Workout Viewer Script

This script allows viewing all workouts for a specific user in a readable format.
It can export workouts to JSON for HTML visualization or display them in the console.

Usage:
    - Set USER_ID variable to the UUID of the user you want to view
    - Run the script to get formatted workout data
    - Optionally export to JSON for HTML viewer
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID
import os
from dotenv import load_dotenv

# --- Setup Paths and Environment ---
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent  # Resolves to the 'backend' directory
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.production"
if dotenv_path.exists():
    print(f"Loading environment variables from: {dotenv_path}")
    load_dotenv(dotenv_path=dotenv_path)
else:
    print(f"Warning: '.env' file not found at '{dotenv_path}'.")

from app.llm.utils.db_utils import create_db_session
from app.models.workout_model import Workout, WorkoutStatusEnum
from app.models.block_model import Block
from app.models.exercise_model import Exercise
from app.models.set_model import Set, SetStatus
from sqlmodel import select
from sqlalchemy.orm import selectinload

# --- Configuration ---
# Set the user ID you want to view workouts for
USER_ID = "bb9ccd12-9018-4303-b870-fe31c94bd7b0"  # Replace with actual UUID

# Output configuration
OUTPUT_DIR = Path(__file__).parent / "output"
JSON_OUTPUT_FILE = OUTPUT_DIR / "user_workouts.json"
HTML_OUTPUT_FILE = OUTPUT_DIR / "user_workout_viewer.html"

async def get_user_workouts(user_id: str, limit: Optional[int] = None) -> List[Workout]:
    """
    Fetch all workouts for a specific user with full relationship loading.
    
    Args:
        user_id: UUID string of the user
        limit: Optional limit on number of workouts to fetch
        
    Returns:
        List of Workout objects with all related data loaded
    """
    print(f"🔍 Fetching workouts for user: {user_id}")
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        print(f"❌ Invalid UUID format: {user_id}")
        return []
    
    async for session in create_db_session(use_production=True):
        try:
            # Build query with eager loading of all relationships
            query = (
                select(Workout)
                .options(
                    selectinload(Workout.blocks)
                    .selectinload(Block.exercises)
                    .selectinload(Exercise.sets)
                )
                .where(Workout.user_id == user_uuid)
                .order_by(Workout.date_created.desc())
            )
            
            if limit:
                query = query.limit(limit)
            
            result = await session.execute(query)
            workouts = result.scalars().all()
            
            print(f"✅ Found {len(workouts)} workouts for user")
            return workouts
            
        except Exception as e:
            print(f"❌ Error fetching workouts: {e}")
            return []

def format_workout_for_display(workout: Workout) -> Dict[str, Any]:
    """
    Format a workout object into a display-friendly dictionary structure.
    
    Args:
        workout: Workout object with loaded relationships
        
    Returns:
        Dictionary with formatted workout data
    """
    # Get sorted blocks
    sorted_blocks = workout.get_sorted_blocks()
    
    # Calculate completion statistics
    total_sets = 0
    completed_sets = 0
    total_exercises = 0
    
    for block in sorted_blocks:
        for exercise in block.exercises:
            total_exercises += 1
            for set_obj in exercise.sets:
                total_sets += 1
                if set_obj.status == SetStatus.done:
                    completed_sets += 1
    
    completion_percentage = (completed_sets / total_sets * 100) if total_sets > 0 else 0
    
    # Format blocks
    formatted_blocks = []
    for block in sorted_blocks:
        formatted_exercises = []
        
        # Group exercises by superset
        superset_groups = {}
        single_exercises = []
        
        for exercise in block.exercises:
            if exercise.superset_id:
                if exercise.superset_id not in superset_groups:
                    superset_groups[exercise.superset_id] = []
                superset_groups[exercise.superset_id].append(exercise)
            else:
                single_exercises.append(exercise)
        
        # Sort exercises within supersets and single exercises
        for superset_id, exercises in superset_groups.items():
            exercises.sort(key=lambda x: x.position or 0)
        
        single_exercises.sort(key=lambda x: x.position or 0)
        
        # Format all exercises
        for exercise in single_exercises:
            formatted_exercises.append(format_exercise(exercise))
        
        for superset_id, exercises in superset_groups.items():
            formatted_superset = {
                "type": "superset",
                "superset_id": superset_id,
                "exercises": [format_exercise(ex) for ex in exercises]
            }
            formatted_exercises.append(formatted_superset)
        
        formatted_blocks.append({
            "name": block.name,
            "description": block.description,
            "notes": block.notes,
            "position": block.position,
            "exercises": formatted_exercises
        })
    
    return {
        "id": workout.id,
        "name": workout.name,
        "description": workout.description,
        "duration": workout.duration,
        "focus": workout.focus,
        "notes": workout.notes,
        "muscle_group_load": workout.muscle_group_load,
        "focus_derivation": workout.focus_derivation,
        "date_created": workout.date_created.isoformat() if workout.date_created else None,
        "status": workout.status.value,
        "blocks": formatted_blocks,
        "statistics": {
            "total_blocks": len(sorted_blocks),
            "total_exercises": total_exercises,
            "total_sets": total_sets,
            "completed_sets": completed_sets,
            "completion_percentage": round(completion_percentage, 1)
        }
    }

def format_exercise(exercise: Exercise) -> Dict[str, Any]:
    """
    Format an exercise object for display.
    
    Args:
        exercise: Exercise object with loaded sets
        
    Returns:
        Dictionary with formatted exercise data
    """
    # Sort sets by position
    sorted_sets = sorted(exercise.sets, key=lambda x: x.position or 0)
    
    formatted_sets = []
    for set_obj in sorted_sets:
        set_data = {
            "position": set_obj.position,
            "status": set_obj.status.value,
            "completed_at": set_obj.completed_at.isoformat() if set_obj.completed_at else None,
            "values": [
                set_obj.reps,
                set_obj.weight,
                set_obj.duration,
                set_obj.distance,
                set_obj.rest_time
            ]
        }
        formatted_sets.append(set_data)
    
    return {
        "id": exercise.id,
        "name": exercise.name,
        "description": exercise.description,
        "notes": exercise.notes,
        "superset_id": exercise.superset_id,
        "position": exercise.position,
        "sets": formatted_sets
    }

def export_workouts_to_json(workouts: List[Workout], output_file: Path) -> None:
    """
    Export formatted workouts to JSON file.
    
    Args:
        workouts: List of Workout objects
        output_file: Path to output JSON file
    """
    formatted_workouts = [format_workout_for_display(workout) for workout in workouts]
    
    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Prepare export data
    export_data = {
        "export_date": datetime.now().isoformat(),
        "user_id": USER_ID,
        "total_workouts": len(formatted_workouts),
        "workouts": formatted_workouts
    }
    
    # Write to JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Exported {len(formatted_workouts)} workouts to {output_file}")

def print_workout_summary(workout: Workout) -> None:
    """
    Print a summary of a workout to the console.
    
    Args:
        workout: Workout object to display
    """
    formatted = format_workout_for_display(workout)
    stats = formatted["statistics"]
    
    print(f"\n{'='*80}")
    print(f"🏋️  WORKOUT: {formatted['name']}")
    print(f"{'='*80}")
    print(f"📅 Created: {formatted['date_created']}")
    print(f"⏱️  Duration: {formatted['duration']} min" if formatted['duration'] else "⏱️  Duration: N/A")
    print(f"🎯 Focus: {formatted['focus']}" if formatted['focus'] else "🎯 Focus: N/A")
    print(f"📊 Status: {formatted['status'].upper()}")
    print(f"📈 Progress: {stats['completed_sets']}/{stats['total_sets']} sets ({stats['completion_percentage']}%)")
    
    if formatted['description']:
        print(f"📝 Description: {formatted['description']}")
    
    if formatted['muscle_group_load']:
        print(f"💪 Muscle Groups: {', '.join(formatted['muscle_group_load'])}")
    
    print(f"\n📋 BLOCKS ({stats['total_blocks']}):")
    print("-" * 40)
    
    for i, block in enumerate(formatted['blocks'], 1):
        print(f"\n{i}. {block['name']}")
        if block['description']:
            print(f"   Description: {block['description']}")
        
        exercise_count = len([ex for ex in block['exercises'] if isinstance(ex, dict) and 'name' in ex])
        superset_count = len([ex for ex in block['exercises'] if isinstance(ex, dict) and ex.get('type') == 'superset'])
        
        print(f"   Exercises: {exercise_count} single, {superset_count} supersets")
        
        for exercise in block['exercises']:
            if isinstance(exercise, dict) and exercise.get('type') == 'superset':
                print(f"   🔄 Superset {exercise['superset_id']}:")
                for ex in exercise['exercises']:
                    set_count = len(ex['sets'])
                    completed_sets = len([s for s in ex['sets'] if s['status'] == 'done'])
                    print(f"      • {ex['name']} ({completed_sets}/{set_count} sets)")
            elif isinstance(exercise, dict):
                set_count = len(exercise['sets'])
                completed_sets = len([s for s in exercise['sets'] if s['status'] == 'done'])
                print(f"   • {exercise['name']} ({completed_sets}/{set_count} sets)")

def print_user_statistics(workouts: List[Workout]) -> None:
    """
    Print overall statistics for the user's workouts.
    
    Args:
        workouts: List of user's workouts
    """
    if not workouts:
        print("📊 No workouts found for user")
        return
    
    total_workouts = len(workouts)
    completed_workouts = len([w for w in workouts if w.status == WorkoutStatusEnum.DONE])
    started_workouts = len([w for w in workouts if w.status == WorkoutStatusEnum.STARTED])
    not_started = len([w for w in workouts if w.status == WorkoutStatusEnum.NOT_STARTED])
    
    total_sets = 0
    completed_sets = 0
    total_exercises = 0
    
    for workout in workouts:
        for block in workout.get_sorted_blocks():
            for exercise in block.exercises:
                total_exercises += 1
                for set_obj in exercise.sets:
                    total_sets += 1
                    if set_obj.status == SetStatus.done:
                        completed_sets += 1
    
    print(f"\n{'='*80}")
    print(f"📊 USER WORKOUT STATISTICS")
    print(f"{'='*80}")
    print(f"Total Workouts: {total_workouts}")
    print(f"✅ Completed: {completed_workouts}")
    print(f"🔄 Started: {started_workouts}")
    print(f"⏳ Not Started: {not_started}")
    print(f"Total Exercises: {total_exercises}")
    print(f"Total Sets: {total_sets}")
    print(f"Completed Sets: {completed_sets}")
    
    if total_sets > 0:
        completion_rate = (completed_sets / total_sets) * 100
        print(f"Overall Completion Rate: {completion_rate:.1f}%")
    
    if total_workouts > 0:
        completion_rate_workouts = (completed_workouts / total_workouts) * 100
        print(f"Workout Completion Rate: {completion_rate_workouts:.1f}%")

async def main():
    """
    Main function to run the user workout viewer.
    """
    print(f"🚀 User Workout Viewer")
    print(f"User ID: {USER_ID}")
    print(f"{'='*50}")
    
    # Fetch workouts
    workouts = await get_user_workouts(USER_ID)
    
    if not workouts:
        print("❌ No workouts found for this user")
        return
    
    # Print user statistics
    print_user_statistics(workouts)
    
    # Print detailed workout summaries
    print(f"\n📋 DETAILED WORKOUT SUMMARIES")
    print(f"{'='*50}")
    
    for workout in workouts:
        print_workout_summary(workout)
    
    # Export to JSON for HTML viewer
    print(f"\n💾 Exporting to JSON...")
    export_workouts_to_json(workouts, JSON_OUTPUT_FILE)
    
    print(f"\n✅ Analysis complete!")
    print(f"📁 JSON file: {JSON_OUTPUT_FILE}")
    print(f"🌐 Open the HTML viewer to see the visual representation")

if __name__ == "__main__":
    asyncio.run(main()) 