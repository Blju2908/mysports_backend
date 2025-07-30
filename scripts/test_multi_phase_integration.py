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

from app.services.workout_generation.multi_phase_orchestrator import create_multi_phase_workout


async def test_phase_1_set_based():
    """Test Phase 1 with set-based muscle fatigue analysis"""
    
    # Test user ID that matches our local training history
    test_user_id = UUID("df668bed-9092-4035-82fa-c68e6fa2a8ff")
    
    try:
        print("🧪 TESTING SET-BASED MUSCLE FATIGUE (Phase 1 Only)")
        print("="*70)
        
        # Test Phase 1 only with set-based method
        result = await create_multi_phase_workout(
            user_id=test_user_id,
            phases_enabled={1: True, 2: False, 3: False, 4: False, 5: False},
            use_local_data=True,
            muscle_fatigue_method="set_based",
            days_lookback=7
        )
        
        if not result.get("success"):
            print(f"❌ Phase 1 failed: {result.get('error', 'Unknown error')}")
            return result
        
        # Display set-based results
        phase_1_data = result['phase_1_results']
        
        if 'set_progress' in phase_1_data:
            print(f"\n🏋️  WÖCHENTLICHE SET-ÜBERSICHT (Letzte 7 Tage)")
            print("="*70)
            
            set_progress = phase_1_data['set_progress']
            
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
            if 'weekly_summary' in phase_1_data:
                summary = phase_1_data['weekly_summary']
                print("\n📊 ZUSAMMENFASSUNG:")
                print(f"🎯 Erreichte Ziele: {summary['muscles_at_target']}/{summary['total_muscle_groups']} Muskelgruppen")
                print(f"📈 Durchschnittliche Zielerreichung: {summary['overall_completion_avg']:.1f}%")
        
        return result
        
    except Exception as e:
        print("\n❌ Error during Phase 1 testing:")
        print(f"   Error Type: {type(e).__name__}")
        print(f"   Error Message: {str(e)}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        raise





if __name__ == "__main__":
    print("🧪 Phase 1 Set-Based Muscle Fatigue Test")
    print()
    
    # Run Phase 1 only test with set-based method
    asyncio.run(test_phase_1_set_based())