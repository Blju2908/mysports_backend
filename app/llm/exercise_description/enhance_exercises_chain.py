"""
LLM chain for enhancing existing exercise descriptions with new fields.
"""
import sys
from pathlib import Path
import asyncio
import json
import os
from typing import List, Dict, Any
from langchain_openai import ChatOpenAI

# Path setup
BACKEND_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BACKEND_DIR))

from app.llm.exercise_description.enhanced_exercise_schemas import (
    ExerciseSchema,
    ExerciseListResponse
)
import logging

logger = logging.getLogger(__name__)

ENHANCEMENT_PROMPT_FILE = "exercise_enhancement_prompt.md"

async def enhance_exercise_descriptions_batch(existing_exercises: List[Dict[str, Any]]) -> List[ExerciseSchema]:
    """
    Enhance a batch of existing exercise descriptions with new fields using OpenAI.
    
    Args:
        existing_exercises: List of existing exercise descriptions as dicts
        
    Returns:
        List of enhanced exercise descriptions
    """
    if not existing_exercises:
        return []
    
    logger.info(f"🤖 Enhancing batch of {len(existing_exercises)} exercises...")
    
    # Load the enhancement prompt template
    prompt_path = Path(__file__).parent / ENHANCEMENT_PROMPT_FILE
    with open(prompt_path, "r", encoding="utf-8") as f:
        prompt_template_content = f.read()
    
    # Create exercise list for the prompt - just dump all data
    exercise_list = []
    for i, exercise in enumerate(existing_exercises):
        exercise_info = f"""
**Übung {i+1}:**
{json.dumps(exercise, indent=2, ensure_ascii=False)}
"""
        exercise_list.append(exercise_info)
    
    exercises_text = "\n".join(exercise_list)
    
    # Format the prompt - use replace to avoid issues with curly braces in JSON
    formatted_prompt = prompt_template_content.replace("{{exercise_list}}", exercises_text)
    
    # API Key from environment
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY2")
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY2 environment variable is not set")
    
    # OpenAI configuration with reasoning
    reasoning = {
        "effort": "medium", 
        "summary": None
    }
    
    llm = ChatOpenAI(
        model="o4-mini",
        api_key=OPENAI_API_KEY,
        use_responses_api=True,
        model_kwargs={"reasoning": reasoning}
    )
    
    # Structured Output
    structured_llm = llm.with_structured_output(ExerciseListResponse)
    
    logger.info("🔄 Sending enhancement request to OpenAI...")
    
    try:
        # API Call with structured output
        response = await structured_llm.ainvoke(formatted_prompt)
        
        logger.info(f"✅ Successfully enhanced {len(response.exercises)} exercise descriptions")
        logger.debug(f"Raw response: {response}")
        return response.exercises
        
    except Exception as e:
        logger.error(f"❌ Error in enhancement processing: {e}")
        import traceback
        traceback.print_exc()
        return []

async def enhance_exercises_with_batching(
    existing_exercises: List[Dict[str, Any]], 
    batch_size: int = 5,
    delay_between_batches: float = 3.0,
    intermediate_save_callback=None
) -> List[ExerciseSchema]:
    """
    Process a large list of exercises in batches for enhancement.
    
    Args:
        existing_exercises: Complete list of existing exercise descriptions
        batch_size: Number of exercises per batch (smaller for complex enhancement)
        delay_between_batches: Pause between batches in seconds
        intermediate_save_callback: Optional callback to save progress after each batch
    
    Returns:
        Complete list of enhanced exercise descriptions
    """
    if not existing_exercises:
        return []
    
    logger.info(f"🏋️ Enhancing {len(existing_exercises)} exercises...")
    
    # Split into batches
    batches = [
        existing_exercises[i:i + batch_size] 
        for i in range(0, len(existing_exercises), batch_size)
    ]
    
    total_batches = len(batches)
    all_enhanced_exercises = []
    
    logger.info(f"📊 Processing {total_batches} batches (batch size: {batch_size})")
    
    for i, batch_exercises in enumerate(batches, 1):
        logger.info(f"🔄 Processing batch {i}/{total_batches}...")
        
        try:
            # Process the current batch
            batch_results = await enhance_exercise_descriptions_batch(batch_exercises)
            
            if batch_results:
                all_enhanced_exercises.extend(batch_results)
            
            logger.info(f"✅ Batch {i}/{total_batches} completed ({len(batch_results)} exercises)")
            
            # Save intermediate progress if callback provided
            if intermediate_save_callback and all_enhanced_exercises:
                try:
                    await intermediate_save_callback(all_enhanced_exercises)
                    logger.info(f"💾 Intermediate save completed ({len(all_enhanced_exercises)} exercises)")
                except Exception as e:
                    logger.warning(f"⚠️ Intermediate save failed: {e}")
            
            # Pause between batches (except for the last one)
            if i < total_batches:
                logger.info(f"⏱️ Waiting {delay_between_batches}s before next batch...")
                await asyncio.sleep(delay_between_batches)
                
        except Exception as e:
            logger.error(f"❌ Error processing batch {i}/{total_batches}: {e}")
            logger.info(f"📝 Successfully processed: {len(all_enhanced_exercises)} exercises so far")
            # Continue with next batch instead of breaking
            continue
    
    logger.info(f"🎉 Completed enhancement! Total exercises processed: {len(all_enhanced_exercises)}")
    return all_enhanced_exercises

async def save_enhanced_exercises_to_json(exercises: List[ExerciseSchema], output_path: Path) -> None:
    """
    Save enhanced exercise descriptions to JSON file.
    
    Args:
        exercises: List of enhanced exercise descriptions
        output_path: Path where to save the JSON file
    """
    try:
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict format
        exercises_data = [exercise.model_dump() for exercise in exercises]
        
        # Save to JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(exercises_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"💾 Saved {len(exercises)} enhanced exercise descriptions to {output_path}")
        
    except Exception as e:
        logger.error(f"❌ Error saving enhanced exercises to JSON: {e}")
        raise