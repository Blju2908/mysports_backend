"""
LLM Documentation Utilities

Provides common functions for documenting LLM chain inputs and outputs
for debugging and analysis purposes.
"""

import os
import json
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel


async def document_llm_input(
    prompt: str, 
    chain_name: str,
    output_dir: Optional[str] = None,
    timestamp: Optional[str] = None
) -> None:
    """
    Document the input prompt of an LLM chain.
    
    Args:
        prompt: The formatted prompt sent to the LLM
        chain_name: Name of the chain (e.g., 'workout_generation', 'workout_revision')
        output_dir: Optional custom output directory
        timestamp: Optional custom timestamp string
    """
    try:
        if output_dir is None:
            # Default to the calling chain's output directory
            import inspect
            caller_file = inspect.stack()[1].filename
            caller_dir = os.path.dirname(caller_file)
            output_dir = os.path.join(caller_dir, "output")
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use provided timestamp or generate current one
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Create filename with chain name and timestamp
        file_name = f"{timestamp}_{chain_name}_input.md"
        file_path = os.path.join(output_dir, file_name)
        
        # Write prompt to file (simplified, no metadata header)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(prompt)
            
        print(f"[LLM_DOCS] Input documented: {file_path}")
        
    except Exception as e:
        print(f"Error in document_llm_input: {e}")
        import traceback
        traceback.print_exc()


async def document_llm_output(
    output_schema: BaseModel,
    chain_name: str,
    output_dir: Optional[str] = None,
    timestamp: Optional[str] = None,
    include_metadata: bool = False
) -> None:
    """
    Document the output of an LLM chain.
    
    Args:
        output_schema: The Pydantic schema instance returned by the LLM
        chain_name: Name of the chain (e.g., 'workout_generation', 'workout_revision')
        output_dir: Optional custom output directory
        timestamp: Optional custom timestamp string
        include_metadata: Whether to include metadata wrapper (default: False)
    """
    try:
        if output_dir is None:
            # Default to the calling chain's output directory
            import inspect
            caller_file = inspect.stack()[1].filename
            caller_dir = os.path.dirname(caller_file)
            output_dir = os.path.join(caller_dir, "output")
        
        # Ensure output directory exists
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Use provided timestamp or generate current one
        if timestamp is None:
            timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        
        # Create filename with chain name and timestamp
        file_name = f"{timestamp}_{chain_name}_output.json"
        file_path = os.path.join(output_dir, file_name)
        
        # Prepare output data - simple or with metadata
        if include_metadata:
            output_data = {
                "metadata": {
                    "timestamp": timestamp,
                    "chain_name": chain_name,
                    "schema_type": output_schema.__class__.__name__
                },
                "data": output_schema.model_dump()
            }
        else:
            # Just the raw schema output
            output_data = output_schema.model_dump()
        
        # Write output to file
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)
            
        print(f"[LLM_DOCS] Output documented: {file_path}")
        
    except Exception as e:
        print(f"Error in document_llm_output: {e}")
        import traceback
        traceback.print_exc()


async def document_llm_session(
    prompt: str,
    output_schema: BaseModel,
    chain_name: str,
    output_dir: Optional[str] = None,
    include_metadata: bool = False
) -> str:
    """
    Document both input and output of an LLM session with matching timestamps.
    
    Args:
        prompt: The formatted prompt sent to the LLM
        output_schema: The Pydantic schema instance returned by the LLM
        chain_name: Name of the chain
        output_dir: Optional custom output directory
        include_metadata: Whether to include metadata in output (default: False)
        
    Returns:
        str: The timestamp used for both files
    """
    # Generate single timestamp for both files
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    
    # Document both input and output with same timestamp
    await document_llm_input(prompt, chain_name, output_dir, timestamp)
    await document_llm_output(output_schema, chain_name, output_dir, timestamp, include_metadata)
    
    return timestamp 