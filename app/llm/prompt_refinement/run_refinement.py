#!/usr/bin/env python3
"""
Main script to run the prompt refinement system.

This script provides an easy way to run the self-improving prompt system
with configurable parameters.
"""

import sys
import asyncio
from pathlib import Path

# Setup paths
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

# Load environment
from dotenv import load_dotenv
dotenv_path = BACKEND_DIR / ".env.development"
load_dotenv(dotenv_path=dotenv_path)

from app.llm.prompt_refinement.refinement_system import run_prompt_refinement


# 🎯 CONFIGURATION - Easy to modify!
CONFIG = {
    "USER_ID": "df668bed-9092-4035-82fa-c68e6fa2a8ff",  # Replace with your user ID
    "MAX_ITERATIONS": 10,                                 # Number of refinement iterations
    "PROVIDER": "openai",                               # LLM provider: "openai", "anthropic", "google"
    "MODEL_NAME": "o4-mini",                             # Model name
    "USE_PRODUCTION_DB": False,                         # True for production, False for dev
    "SAVE_ITERATIONS": True,                            # Save detailed iteration results
}


async def main():
    """Main function to run the prompt refinement system"""
    
    print("🚀 S3ssions Prompt Refinement System")
    print("=" * 60)
    print("This system will:")
    print("1. 🔍 Analyze current workout generation quality")
    print("2. ⚡ Identify weaknesses and improvements")
    print("3. 🔄 Refine the system prompt iteratively")
    print("4. ✅ Validate improvements with A/B testing")
    print("5. 💾 Save all results and updated prompts")
    print("=" * 60)
    
    # Display configuration
    print(f"📊 Configuration:")
    print(f"   - User ID: {CONFIG['USER_ID']}")
    print(f"   - Max iterations: {CONFIG['MAX_ITERATIONS']}")
    print(f"   - LLM Provider: {CONFIG['PROVIDER']}")
    print(f"   - Model: {CONFIG['MODEL_NAME']}")
    print(f"   - Database: {'🚀 Production' if CONFIG['USE_PRODUCTION_DB'] else '💻 Development'}")
    print(f"   - Save iterations: {'✅ Yes' if CONFIG['SAVE_ITERATIONS'] else '❌ No'}")
    print("=" * 60)
    
    # Confirm before starting
    try:
        confirm = input("\n▶️ Press Enter to start refinement, or Ctrl+C to cancel: ")
    except KeyboardInterrupt:
        print("\n❌ Refinement cancelled by user")
        return
    
    # Run the refinement system
    try:
        results = await run_prompt_refinement(
            user_id=CONFIG["USER_ID"],
            max_iterations=CONFIG["MAX_ITERATIONS"],
            provider=CONFIG["PROVIDER"],
            model_name=CONFIG["MODEL_NAME"],
            use_production_db=CONFIG["USE_PRODUCTION_DB"],
            save_iterations=CONFIG["SAVE_ITERATIONS"]
        )
        
        # Display final summary
        print("\n" + "🎉 REFINEMENT COMPLETE!" + "\n")
        
        if results:
            print("📈 Iteration Summary:")
            for i, result in enumerate(results, 1):
                status = "✅ Improved" if result.improved else "❌ No improvement"
                print(f"   {i}. Score: {result.critique.overall_score}/10 - {status}")
            
            # Show key insights
            final_result = results[-1]
            print(f"\n💡 Key Insights:")
            print(f"   - Final critique score: {final_result.critique.overall_score}/10")
            print(f"   - Total improvements: {sum(1 for r in results if r.improved)}")
            print(f"   - Success rate: {sum(1 for r in results if r.improved)/len(results)*100:.1f}%")
            
            if final_result.critique.key_improvements:
                print(f"\n🔍 Final Key Improvements:")
                for improvement in final_result.critique.key_improvements:
                    print(f"   - {improvement}")
            
            print(f"\n📁 Results saved to: backend/app/llm/prompt_refinement/output/")
            print(f"📝 Updated prompt saved to: backend/app/llm/workout_generation/prompts/training_principles_base.md")
        else:
            print("⚠️ No iterations completed")
            
    except Exception as e:
        print(f"❌ Refinement failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 