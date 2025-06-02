import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[3]))
import os
from dotenv import load_dotenv

# Load environment variables
dotenv_path = Path(__file__).resolve().parents[3] / '.env.production'
load_dotenv(dotenv_path=dotenv_path)

import asyncio
import json
from datetime import date, datetime
from typing import List, Optional
from uuid import UUID
from app.db.session import get_engine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from app.llm.training_plan_generation.training_plan_generation_service import run_training_plan_generation
from app.models.training_plan_model import TrainingPlan
from app.models.user_model import UserModel


class TrainingPlanRegenerator:
    """Service class for regenerating training plans for all users"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.errors: List[dict] = []
    
    async def get_all_user_ids_with_training_plans(self) -> List[UUID]:
        """Fetch all user IDs that have training plans"""
        query = (
            select(UserModel.id)
            .where(UserModel.training_plan_id.is_not(None))
        )
        result = await self.db.exec(query)
        user_ids = result.all()
        return list(user_ids)
    
    async def regenerate_training_plan_for_user_id(self, user_id: UUID) -> bool:
        """Regenerate training plan for a specific user ID"""
        user_id_str = str(user_id)
        
        try:
            print(f"🔄 Processing user {user_id_str}...")
            
            # Generate new training plan
            plan_schema = await run_training_plan_generation(
                user_id=user_id, 
                db=self.db
            )
            
            print(f"✅ Successfully regenerated training plan for user {user_id_str}")
            return True
            
        except Exception as e:
            error_info = {
                "user_id": user_id_str,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
            self.errors.append(error_info)
            print(f"❌ Error processing user {user_id_str}: {str(e)}")
            return False
    
    async def regenerate_all_training_plans(self, batch_size: int = 10) -> dict:
        """Regenerate training plans for all users in batches"""
        print("🚀 Starting training plan regeneration for all users...")
        
        # Get all user IDs with training plans
        user_ids = await self.get_all_user_ids_with_training_plans()
        total_users = len(user_ids)
        
        if total_users == 0:
            print("ℹ️ No users with training plans found.")
            return self._get_summary()
        
        print(f"📊 Found {total_users} users with training plans")
        
        # Process user IDs in batches
        for i in range(0, total_users, batch_size):
            batch = user_ids[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (total_users + batch_size - 1) // batch_size
            
            print(f"\n📦 Processing batch {batch_num}/{total_batches} ({len(batch)} users)...")
            
            # Process batch
            for user_id in batch:
                self.processed_count += 1
                success = await self.regenerate_training_plan_for_user_id(user_id)
                
                if success:
                    self.success_count += 1
                else:
                    self.error_count += 1
                
                # Progress indicator
                progress = (self.processed_count / total_users) * 100
                print(f"📈 Progress: {self.processed_count}/{total_users} ({progress:.1f}%)")
            
            # Small delay between batches to avoid overwhelming the system
            if i + batch_size < total_users:
                print("⏳ Waiting 2 seconds before next batch...")
                await asyncio.sleep(2)
        
        return self._get_summary()
    
    def _get_summary(self) -> dict:
        """Get summary of the regeneration process"""
        return {
            "total_processed": self.processed_count,
            "successful": self.success_count,
            "errors": self.error_count,
            "error_details": self.errors,
            "success_rate": (self.success_count / self.processed_count * 100) if self.processed_count > 0 else 0
        }
    
    async def save_error_log(self, filename: str = "training_plan_regeneration_errors.json"):
        """Save error log to file"""
        if self.errors:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.errors, f, ensure_ascii=False, indent=2)
            print(f"📝 Error log saved to {filename}")


async def regenerate_specific_users(user_ids: List[str]) -> dict:
    """Regenerate training plans for specific users only"""
    engine = get_engine()
    
    async with AsyncSession(engine) as session:
        regenerator = TrainingPlanRegenerator(session)
        
        print(f"🎯 Regenerating training plans for {len(user_ids)} specific users...")
        
        for user_id_str in user_ids:
            try:
                user_id = UUID(user_id_str)
                
                # Get user
                query = select(UserModel).where(UserModel.id == user_id)
                result = await session.exec(query)
                user = result.first()
                
                if not user:
                    print(f"⚠️ User {user_id_str} not found")
                    continue
                
                if not user.training_plan_id:
                    print(f"⚠️ User {user_id_str} has no training plan")
                    continue
                
                regenerator.processed_count += 1
                # Store user_id before any operations to avoid session issues
                user_id = user.id
                success = await regenerator.regenerate_training_plan_for_user_id(user_id)
                
                if success:
                    regenerator.success_count += 1
                else:
                    regenerator.error_count += 1
                    
            except ValueError:
                print(f"❌ Invalid UUID: {user_id_str}")
                regenerator.error_count += 1
            except Exception as e:
                print(f"❌ Error processing user {user_id_str}: {str(e)}")
                regenerator.error_count += 1
        
        summary = regenerator._get_summary()
        await regenerator.save_error_log()
        return summary


async def main():
    """Main function with different execution modes"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Regenerate training plans")
    parser.add_argument("--mode", choices=["all", "specific"], default="all", 
                       help="Regeneration mode: 'all' for all users, 'specific' for specific user IDs")
    parser.add_argument("--users", nargs="*", help="User IDs for specific mode")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size for processing")
    parser.add_argument("--dry-run", action="store_true", help="Only show what would be processed")
    
    args = parser.parse_args()
    
    if args.mode == "specific":
        if not args.users:
            print("❌ No user IDs provided for specific mode")
            return
        
        summary = await regenerate_specific_users(args.users)
    else:
        # All users mode
        engine = get_engine()
        
        async with AsyncSession(engine) as session:
            regenerator = TrainingPlanRegenerator(session)
            
            if args.dry_run:
                user_ids = await regenerator.get_all_user_ids_with_training_plans()
                print(f"🔍 DRY RUN: Would process {len(user_ids)} users with training plans")
                for user_id in user_ids[:10]:  # Show first 10 users
                    print(f"  - User ID: {user_id}")
                if len(user_ids) > 10:
                    print(f"  ... and {len(user_ids) - 10} more users")
                return
            
            summary = await regenerator.regenerate_all_training_plans(
                batch_size=args.batch_size
            )
            await regenerator.save_error_log()
    
    # Print summary
    print("\n" + "="*50)
    print("📊 REGENERATION SUMMARY")
    print("="*50)
    print(f"Total processed: {summary['total_processed']}")
    print(f"Successful: {summary['successful']}")
    print(f"Errors: {summary['errors']}")
    print(f"Success rate: {summary['success_rate']:.1f}%")
    
    if summary['errors'] > 0:
        print(f"\n❌ {summary['errors']} errors occurred. Check training_plan_regeneration_errors.json for details.")
    else:
        print("\n🎉 All training plans regenerated successfully!")


if __name__ == "__main__":
    asyncio.run(main()) 