"""
Integration Test for Multi-Phase Workout Generation System

This script tests the Phase 1 Muscle Fatigue Service with real database data
and demonstrates the complete multi-phase workflow.
"""

# Setup environment before importing any app modules
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "utils"))
from script_setup import setup_environment
setup_environment()

import asyncio
from uuid import UUID

from app.services.workout_generation.phase_1_only_orchestrator import run_phase_1_only
from app.services.workout_generation.set_based_muscle_fatigue_service import create_set_based_muscle_fatigue_service


async def test_phase_1_muscle_fatigue_only():
    """Test only Phase 1 (Muscle Fatigue Analysis) using local data"""
    
    # Test user ID that matches our local training history
    test_user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff")
    
    try:
        # Test Phase 1 only
        result = await run_phase_1_only(
            user_id=test_user_id,
            days_lookback=14
        )
        
        if not result.get("success"):
            print(f"❌ Phase 1 failed: {result.get('error', 'Unknown error')}")
            return result
        
        # Display results
        phase_1_data = result['phase_1_results']
        
        print(f"💪 MUSCLE RECOVERY ({phase_1_data['average_recovery']:.1f}% avg):")
        
        # Simple list of all muscles with recovery percentages
        for muscle, recovery_pct in sorted(phase_1_data['muscle_recovery_percentages'].items()):
            status = "🟢" if recovery_pct >= 85 else "🟡" if recovery_pct >= 70 else "🔴"
            print(f"   {status} {muscle}: {recovery_pct}%")
        
        return result
        
    except Exception as e:
        print("\n❌ Error during Phase 1 testing:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise


async def test_set_based_muscle_fatigue():
    """Test the new set-based muscle fatigue service using local data"""
    
    # Test user ID that matches our local training history
    test_user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff")
    
    try:
        print("\n🧪 TESTING SET-BASED MUSCLE FATIGUE SERVICE")
        print("="*70)
        
        # Create service instance
        service = create_set_based_muscle_fatigue_service()
        print(f"✅ Service erstellt - {len(service.exercise_descriptions)} Übungsbeschreibungen geladen")
        
        # Load real training history using existing orchestrator function
        from app.services.workout_generation.phase_1_only_orchestrator import load_local_training_history
        training_history = load_local_training_history(test_user_id)
        
        if not training_history:
            print("❌ Keine Trainingsdaten gefunden")
            return {"success": False, "error": "No training data"}
        
        print(f"✅ Trainingsdaten geladen - {len(training_history)} Übungen gefunden")
        
        # Convert Phase1ExerciseRead to simple format for set-based service
        simple_exercises = []
        for exercise in training_history:
            # Create simple exercise object with just name and sets
            simple_exercise_data = {
                'name': exercise.name,
                'sets': []
            }
            
            # Convert sets to simple format
            for set_data in exercise.sets:
                simple_set = {
                    'reps': set_data.reps,
                    'weight': set_data.weight, 
                    'duration': set_data.duration,
                    'distance': getattr(set_data, 'distance', None),
                    'completed_at': set_data.completed_at
                }
                simple_exercise_data['sets'].append(simple_set)
            
            simple_exercises.append(simple_exercise_data)
        
        print("\n🏋️  WÖCHENTLICHE SET-ÜBERSICHT (Letzte 7 Tage)")
        print("="*70)
        
        # Calculate with real data
        set_progress = service.calculate_weekly_set_progress(simple_exercises, days_lookback=7)
        
        # Sort by current sets (descending) for better readability
        sorted_muscles = sorted(
            set_progress.items(), 
            key=lambda x: x[1]["current_sets"], 
            reverse=True
        )
        
        # Display results
        for muscle, progress in sorted_muscles:
            current = progress["current_sets"]
            target = progress["target_sets"]
            completion = progress["completion_percentage"]
            remaining = progress["remaining_sets"]
            
            # Choose emoji based on completion
            if completion >= 100:
                emoji = "✅"
            elif completion >= 80:
                emoji = "🔶"
            elif completion >= 50:
                emoji = "🔸"
            else:
                emoji = "⚪"
            
            display_name = muscle.replace("_", " ").title()
            print(f"{emoji} {display_name:20} {current:4.1f}/{target:2} Sets ({completion:5.1f}%) - Noch {remaining:4.1f} Sets")
        
        # Get summary
        summary = service.get_weekly_summary(set_progress)
        print("\n📊 ZUSAMMENFASSUNG:")
        print(f"🎯 Erreichte Ziele: {summary['muscles_at_target']}/{summary['total_muscle_groups']} Muskelgruppen")
        print(f"📈 Durchschnittliche Zielerreichung: {summary['overall_completion_avg']:.1f}%")
        
        print("\n✅ SET-BASIERTES MODELL ERFOLGREICH GETESTET")
        return {"success": True, "set_progress": set_progress, "summary": summary}
        
    except Exception as e:
        print("\n❌ Error during set-based testing:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise




if __name__ == "__main__":
    print("🧪 Phase 1 Muscle Fatigue Analysis Test")
    print()
    
    # Run Phase 1 only test with local data
    asyncio.run(test_phase_1_muscle_fatigue_only())
    
    # Run new set-based muscle fatigue test
    asyncio.run(test_set_based_muscle_fatigue())