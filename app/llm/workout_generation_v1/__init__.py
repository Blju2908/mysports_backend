"""
Workout Generation V1 - Multi-version LLM workout generation

This module provides different versions of workout generation with varying complexity:
- standard: Full-featured workout generation with detailed structure
- minimal: Performance-optimized minimal workout generation

Usage:
    from app.llm.workout_generation_v1.versions.minimal import workout_generation_service_minimal
"""

# Import commonly used items for convenience
from .versions.standard.schemas import CompactWorkoutSchema
from .versions.minimal.service import generate_minimal_workout, MinimalWorkoutInput, MinimalWorkoutOutput

__all__ = [
    "generate_minimal_workout",
    "CompactWorkoutSchema",
    "MinimalWorkoutInput",
    "MinimalWorkoutOutput"
]