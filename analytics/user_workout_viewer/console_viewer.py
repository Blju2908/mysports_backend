"""
Console Workout Viewer

A simple command-line tool to view user workouts in the terminal.
This provides a quick way to see workout summaries without opening a browser.

Usage:
    - Set USER_ID variable to the UUID of the user you want to view
    - Run the script to see formatted workout summaries in the console
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from uuid import UUID
import os
from dotenv import load_dotenv

# --- Setup Paths and Environment ---
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.append(str(BACKEND_DIR))

# Load environment variables
dotenv_path = BACKEND_DIR / ".env.production"
if dotenv_path.exists():
    load_dotenv(dotenv_path=dotenv_path)

from app.llm.utils.db_utils import create_db_session
from app.models.workout_model import Workout, WorkoutStatusEnum
from app.models.set_model import SetStatus

# --- Configuration ---
USER_ID = "your-user-uuid-here"  # Replace with actual UUID
LIMIT = None  # Set to a number to limit results, or None for all

async def get_user_workouts_simple(user_id: str, limit: Optional[int] = None) -> List[Workout]:
    """Fetch workouts for user with minimal data loading for console display."""
    print(f"🔍 Fetching workouts for user: {user_id}")
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        print(f"❌ Invalid UUID format: {user_id}")
        return []
    
    async for session in create_db_session(use_production=True):
        try:
            from sqlmodel import select
            from sqlalchemy.orm import selectinload
            from app.models.block_model import Block
            from app.models.exercise_model import Exercise
            
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
            
            print(f"✅ Found {len(workouts)} workouts")
            return workouts
            
        except Exception as e:
            print(f"❌ Error fetching workouts: {e}")
            return []

def print_workout_summary_simple(workout: Workout, index: int) -> None:
    """Print a simple summary of a workout."""
    sorted_blocks = workout.get_sorted_blocks()
    
    # Calculate basic stats
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
    
    # Print workout header
    print(f"\n{'='*60}")
    print(f"🏋️  WORKOUT #{index + 1}: {workout.name}")
    print(f"{'='*60}")
    
    # Print basic info
    print(f"📅 Created: {workout.date_created.strftime('%Y-%m-%d %H:%M') if workout.date_created else 'N/A'}")
    print(f"⏱️  Duration: {workout.duration} min" if workout.duration else "⏱️  Duration: N/A")
    print(f"🎯 Focus: {workout.focus}" if workout.focus else "🎯 Focus: N/A")
    print(f"📊 Status: {workout.status.value.upper()}")
    print(f"📈 Progress: {completed_sets}/{total_sets} sets ({completion_percentage:.1f}%)")
    
    if workout.description:
        print(f"📝 Description: {workout.description}")
    
    if workout.muscle_group_load:
        print(f"💪 Muscle Groups: {', '.join(workout.muscle_group_load)}")
    
    # Print blocks summary
    print(f"\n📋 BLOCKS ({len(sorted_blocks)}):")
    print("-" * 40)
    
    for i, block in enumerate(sorted_blocks, 1):
        exercise_count = len(block.exercises)
        superset_count = len([ex for ex in block.exercises if ex.superset_id])
        single_count = exercise_count - superset_count
        
        print(f"\n{i}. {block.name}")
        if block.description:
            print(f"   Description: {block.description}")
        
        print(f"   Exercises: {single_count} single, {superset_count} supersets")
        
        # Print exercise summary
        for exercise in block.exercises:
            set_count = len(exercise.sets)
            completed_exercise_sets = len([s for s in exercise.sets if s.status == SetStatus.done])
            
            if exercise.superset_id:
                print(f"   🔄 {exercise.name} (Superset {exercise.superset_id}) - {completed_exercise_sets}/{set_count} sets")
            else:
                print(f"   • {exercise.name} - {completed_exercise_sets}/{set_count} sets")

def print_user_statistics_simple(workouts: List[Workout]) -> None:
    """Print simple user statistics."""
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
    
    print(f"\n{'='*60}")
    print(f"📊 USER WORKOUT STATISTICS")
    print(f"{'='*60}")
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

def print_recent_workouts(workouts: List[Workout], count: int = 5) -> None:
    """Print summary of recent workouts."""
    recent = workouts[:count]
    
    print(f"\n📋 RECENT WORKOUTS (Last {len(recent)}):")
    print("-" * 50)
    
    for i, workout in enumerate(recent, 1):
        sorted_blocks = workout.get_sorted_blocks()
        total_sets = sum(len(exercise.sets) for block in sorted_blocks for exercise in block.exercises)
        completed_sets = sum(
            len([s for s in exercise.sets if s.status == SetStatus.done])
            for block in sorted_blocks for exercise in block.exercises
        )
        
        completion = (completed_sets / total_sets * 100) if total_sets > 0 else 0
        
        print(f"{i}. {workout.name}")
        print(f"   📅 {workout.date_created.strftime('%Y-%m-%d') if workout.date_created else 'N/A'}")
        print(f"   🎯 {workout.focus or 'N/A'}")
        print(f"   📊 {workout.status.value.upper()} - {completion:.1f}% ({completed_sets}/{total_sets} sets)")
        print()

async def main():
    """Main function for console viewer."""
    print(f"🚀 Console Workout Viewer")
    print(f"User ID: {USER_ID}")
    print(f"{'='*50}")
    
    # Fetch workouts
    workouts = await get_user_workouts_simple(USER_ID, LIMIT)
    
    if not workouts:
        print("❌ No workouts found for this user")
        return
    
    # Print user statistics
    print_user_statistics_simple(workouts)
    
    # Print recent workouts summary
    print_recent_workouts(workouts)
    
    # Ask user if they want to see detailed summaries
    print("Möchtest du detaillierte Workout-Zusammenfassungen sehen? (y/n): ", end="")
    try:
        response = input().lower().strip()
        if response in ['y', 'yes', 'ja', 'j']:
            print(f"\n📋 DETAILED WORKOUT SUMMARIES")
            print(f"{'='*50}")
            
            for i, workout in enumerate(workouts):
                print_workout_summary_simple(workout, i)
                
                # Ask if user wants to continue after each workout
                if i < len(workouts) - 1:
                    print("\nWeiter zum nächsten Workout? (y/n): ", end="")
                    try:
                        cont_response = input().lower().strip()
                        if cont_response not in ['y', 'yes', 'ja', 'j']:
                            break
                    except KeyboardInterrupt:
                        print("\nAbgebrochen.")
                        break
    except KeyboardInterrupt:
        print("\nAbgebrochen.")
    
    print(f"\n✅ Console viewer complete!")

if __name__ == "__main__":
    asyncio.run(main()) 