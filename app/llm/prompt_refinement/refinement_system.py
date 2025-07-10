"""
Main refinement system that orchestrates the self-improving prompt loop.
"""

import asyncio
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.llm.utils.db_utils import DatabaseManager
from app.models.training_plan_model import TrainingPlan
from app.db.workout_db_access import get_training_history_for_user_from_db
from app.llm.workout_generation.create_workout_service import format_training_plan_for_llm, format_training_history_for_llm
from app.llm.workout_generation.workout_generation_chain import (
    generate_freeform_workout_for_refinement
)

from .agents import PromptRefinementAgents
from .schemas import RefinementConfig, IterationResult, ValidationDecision, RefinedPrompts
from .prompts import VALUE_PROPOSITION_TEXT


class PromptRefinementSystem:
    """
    Self-improving prompt system that uses multiple LLM agents to
    continuously refine workout generation prompts.
    """
    
    def __init__(self, config: RefinementConfig):
        self.config = config
        self.agents = PromptRefinementAgents(
            provider=config.provider,
            model_name=config.model_name
        )
        self.output_dir = Path(__file__).parent / "output"
        self.output_dir.mkdir(exist_ok=True)
        
    def _get_current_prompts(self) -> (str, str):
        """Loads the current prompt template and training principles."""
        try:
            template_path = Path(__file__).parent.parent / "workout_generation" / "prompts" / "workout_generation_prompt_step1.md"
            with open(template_path, 'r', encoding='utf-8') as f:
                template = f.read()
        except FileNotFoundError:
            print("⚠️ workout_generation_prompt_step1.md not found!")
            template = "{training_principles}" # Minimal fallback

        try:
            principles_path = Path(__file__).parent.parent / "workout_generation" / "prompts" / "training_principles_base.md"
            with open(principles_path, 'r', encoding='utf-8') as f:
                principles = f.read()
        except FileNotFoundError:
            print("⚠️ training_principles_base.md not found!")
            principles = "Create a good workout." # Minimal fallback

        return template, principles
    
    def _save_refined_prompts(self, refined_prompts: RefinedPrompts, iteration: int):
        """Saves the refined prompt template and principles to their files."""
        if not self.config.save_iterations:
            return
            
        # 1. Save refined template
        template_path = Path(__file__).parent.parent / "workout_generation" / "prompts" / "workout_generation_prompt_step1.md"
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(refined_prompts.prompt_template)
        
        # Save backup of the template
        backup_template_path = self.output_dir / f"template_iteration_{iteration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(backup_template_path, 'w', encoding='utf-8') as f:
            f.write(refined_prompts.prompt_template)

        # 2. Save refined principles
        principles_path = Path(__file__).parent.parent / "workout_generation" / "prompts" / "training_principles_base.md"
        with open(principles_path, 'w', encoding='utf-8') as f:
            f.write(refined_prompts.training_principles)

        # Save backup of the principles
        backup_principles_path = self.output_dir / f"principles_iteration_{iteration}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(backup_principles_path, 'w', encoding='utf-8') as f:
            f.write(refined_prompts.training_principles)
        
        print(f"✅ Refined template saved to {template_path.name}")
        print(f"✅ Refined principles saved to {principles_path.name}")

    def _save_iteration_results(self, iteration_results: List[IterationResult]):
        """Save detailed results of all iterations"""
        if not self.config.save_iterations:
            return
            
        results_path = self.output_dir / f"refinement_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Convert to JSON-serializable format
        serializable_results = []
        for result in iteration_results:
            serializable_results.append({
                "iteration": result.iteration,
                "original_prompt": result.original_prompt,
                "critique": result.critique.model_dump(),
                "refined_prompt": result.refined_prompt,
                "original_workout": result.original_workout,
                "refined_workout": result.refined_workout,
                "validation": result.validation.model_dump(),
                "improved": result.improved,
                "timestamp": result.timestamp
            })
        
        with open(results_path, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Iteration results saved to {results_path}")

    async def _load_user_data(self, user_id: UUID, db: AsyncSession) -> str:
        """Load user training plan and history"""
        # Load training plan
        training_plan_db_obj = await db.scalar(
            select(TrainingPlan).where(TrainingPlan.user_id == user_id)
        )
        if not training_plan_db_obj:
            raise ValueError(f"No training plan found for user {user_id}")
        
        formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
        
        # Load training history
        raw_training_history = await get_training_history_for_user_from_db(user_id, db, limit=10)
        formatted_history = format_training_history_for_llm(raw_training_history)
        
        # Combine into single context string
        user_data = f"""# Training Plan
{formatted_training_plan}

# Training History
{formatted_history}"""
        
        return user_data, training_plan_db_obj
    
    async def _generate_workout_with_custom_prompt(
        self,
        custom_training_principles: str,
        user_data_obj: Any,
        user_data_str: str,
        db: AsyncSession
    ) -> str:
        """Generate a freeform workout using a custom set of training principles."""
        
        # Nutzen der neuen, schlanken Funktion, die nur Markdown zurückgibt
        workout_str = await generate_freeform_workout_for_refinement(
            training_plan_obj=user_data_obj,
            training_plan_str=user_data_str.split("# Training History")[0].replace("# Training Plan\n", ""),
            training_history=user_data_str.split("# Training History\n")[1] if "# Training History" in user_data_str else "",
            user_prompt="",
            db=db,
            use_exercise_filtering=False, # Für Konsistenz im Test deaktiviert
            training_principles=custom_training_principles,
        )
        return workout_str
    
    async def run_refinement_loop(self) -> List[IterationResult]:
        """
        Run the main refinement loop.
        
        Returns:
            List of IterationResult objects for each iteration
        """
        print("🚀 Starting Prompt Refinement System")
        print("=" * 60)
        print(f"📊 Configuration:")
        print(f"   - Max iterations: {self.config.max_iterations}")
        print(f"   - LLM Provider: {self.config.provider}")
        print(f"   - Model: {self.config.model_name}")
        print(f"   - User ID: {self.config.user_id}")
        print(f"   - Save iterations: {self.config.save_iterations}")
        print("=" * 60)
        
        user_id = UUID(self.config.user_id)
        db_manager = DatabaseManager(use_production=self.config.use_production_db)
        iteration_results = []
        
        async with await db_manager.get_session() as db:
            try:
                # Load user data once
                user_data_str, user_data_obj = await self._load_user_data(user_id, db)
                
                # Start with current prompts
                current_template, current_principles = self._get_current_prompts()
                
                for iteration in range(1, self.config.max_iterations + 1):
                    print(f"\n🔄 ITERATION {iteration}/{self.config.max_iterations}")
                    print("-" * 50)
                    
                    iteration_start = datetime.now()
                    
                    # Assemble the full prompt for critique agent
                    full_prompt_v1 = current_template.format(
                        training_principles=current_principles,
                        exercise_library="{exercise_library}", # Placeholder for critique
                        current_date=datetime.now().strftime("%d.%m.%Y"),
                        user_prompt="",
                        training_plan="{training_plan}",
                        training_history="{training_history}"
                    )
                    
                    # Generate workout with current prompt
                    print("🏋️ Generating workout with current prompt...")
                    original_workout = await self._generate_workout_with_custom_prompt(
                        current_principles, user_data_obj, user_data_str, db
                    )
                    
                    # Run agents to analyze and improve
                    critique = await self.agents.critique_workout(
                        full_prompt_v1, user_data_str, original_workout
                    )
                    
                    if not critique:
                        print("⚠️ Critique Agent returned nothing. Skipping refinement for this iteration.")
                        continue

                    # If score is already high, consider stopping
                    if critique.overall_score >= 9:
                        print(f"🎯 High score achieved ({critique.overall_score}/10), stopping refinement")
                        break
                    
                    # 3. Refine Prompts
                    print("🧐 Refine Agent: Improving prompts based on critique...")

                    refined_prompts = await self.agents.refine_prompt(
                        current_template, current_principles, critique
                    )

                    if not refined_prompts:
                        print("⚠️ Refinement failed: Refine Agent returned nothing.")
                        continue
                    
                    # Generate workout with refined principles
                    print("🔄 Generating workout with refined prompt...")
                    refined_workout = await self._generate_workout_with_custom_prompt(
                        refined_prompts.training_principles, user_data_obj, user_data_str, db
                    )
                    
                    # Validate which workout is better
                    validation = await self.agents.validate_workouts(
                        user_data_str, original_workout, refined_workout
                    )
                    
                    # Determine if improvement occurred
                    improved = validation.decision == ValidationDecision.WORKOUT_2
                    
                    # Assemble the full refined prompt for logging
                    full_prompt_v2 = refined_prompts.prompt_template.format(
                        training_principles=refined_prompts.training_principles,
                        exercise_library="{exercise_library}",
                        current_date=datetime.now().strftime("%d.%m.%Y"),
                        user_prompt="",
                        training_plan="{training_plan}",
                        training_history="{training_history}"
                    )
                    
                    # Create iteration result
                    iteration_result = IterationResult(
                        iteration=iteration,
                        original_prompt=full_prompt_v1,
                        critique=critique,
                        refined_prompt=full_prompt_v2,
                        original_workout=original_workout,
                        refined_workout=refined_workout,
                        validation=validation,
                        improved=improved,
                        timestamp=datetime.now().isoformat()
                    )
                    
                    iteration_results.append(iteration_result)
                    
                    # Print iteration summary
                    print(f"📊 Iteration {iteration} Summary:")
                    print(f"   - Critique Score: {critique.overall_score}/10")
                    print(f"   - Validation: {validation.decision.value}")
                    print(f"   - Improved: {'✅' if improved else '❌'}")
                    print(f"   - Duration: {(datetime.now() - iteration_start).total_seconds():.1f}s")
                    
                    # If improved, use the refined prompts for next iteration
                    if improved:
                        current_template = refined_prompts.prompt_template
                        current_principles = refined_prompts.training_principles
                        self._save_refined_prompts(refined_prompts, iteration)
                        print("🎉 Prompts updated with improvements!")
                    else:
                        print("⚠️ No improvement detected, keeping current prompts")
                    
                    # Show weaknesses and improvements
                    if critique.weaknesses:
                        print("\n🔍 Identified Weaknesses:")
                        for i, weakness in enumerate(critique.weaknesses, 1):
                            print(f"   {i}. {weakness.category}: {weakness.issue}")
                    
                    if critique.key_improvements:
                        print("\n💡 Key Improvements:")
                        for i, improvement in enumerate(critique.key_improvements, 1):
                            print(f"   {i}. {improvement}")
                
                # Save all iteration results
                self._save_iteration_results(iteration_results)
                
                # Final summary
                print("\n" + "=" * 60)
                print("🎯 REFINEMENT COMPLETE")
                print("=" * 60)
                
                improved_count = sum(1 for r in iteration_results if r.improved)
                final_score = iteration_results[-1].critique.overall_score if iteration_results else 0
                
                print(f"📊 Final Results:")
                print(f"   - Total iterations: {len(iteration_results)}")
                print(f"   - Successful improvements: {improved_count}")
                print(f"   - Final critique score: {final_score}/10")
                print(f"   - Success rate: {improved_count/len(iteration_results)*100:.1f}%")
                
                return iteration_results
                
            except Exception as e:
                print(f"❌ Refinement failed: {e}")
                import traceback
                traceback.print_exc()
                return iteration_results
                
            finally:
                await db_manager.close()

# Convenience function for easy execution
async def run_prompt_refinement(
    user_id: str,
    max_iterations: int = 3,
    provider: str = "openai",
    model_name: str = "gpt-4o",
    use_production_db: bool = False,
    save_iterations: bool = True
) -> List[IterationResult]:
    """
    Convenience function to run the prompt refinement system.
    
    Args:
        user_id: User ID to use for testing
        max_iterations: Maximum number of refinement iterations
        provider: LLM provider ('openai', 'anthropic', 'google')
        model_name: Model name to use
        use_production_db: Whether to use production database
        save_iterations: Whether to save iteration results
    
    Returns:
        List of IterationResult objects
    """
    config = RefinementConfig(
        max_iterations=max_iterations,
        provider=provider,
        model_name=model_name,
        use_production_db=use_production_db,
        save_iterations=save_iterations,
        user_id=user_id
    )
    
    system = PromptRefinementSystem(config)
    return await system.run_refinement_loop() 