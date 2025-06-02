#!/usr/bin/env python3
"""
Simple batch regeneration script for training plans.
This script regenerates all training plans in the new JSON format.
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = Path(__file__).resolve().parents[3] / '.env.development'
load_dotenv(dotenv_path=dotenv_path)

import asyncio
from app.db.session import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from regenerate_all_training_plans import TrainingPlanRegenerator


async def simple_regenerate_all():
    """Simple function to regenerate all training plans"""
    print("🚀 Starting simple training plan regeneration...")
    
    engine = get_engine()
    
    async with AsyncSession(engine) as session:
        regenerator = TrainingPlanRegenerator(session)
        
        # Use smaller batch size for safer processing
        summary = await regenerator.regenerate_all_training_plans(batch_size=5)
        await regenerator.save_error_log()
    
    # Print results
    print("\n" + "="*50)
    print("📊 REGENERATION COMPLETE")
    print("="*50)
    print(f"✅ Successfully processed: {summary['successful']}")
    print(f"❌ Errors: {summary['errors']}")
    print(f"📈 Success rate: {summary['success_rate']:.1f}%")
    
    if summary['errors'] > 0:
        print(f"\n⚠️ Check 'training_plan_regeneration_errors.json' for error details.")
    
    return summary


if __name__ == "__main__":
    asyncio.run(simple_regenerate_all()) 