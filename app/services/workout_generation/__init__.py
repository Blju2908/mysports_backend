"""
Multi-Phase Workout Generation System

A modular approach to workout generation that reduces LLM dependency
by separating analytical tasks from creative design.

Phases:
1. Muscle Fatigue Analysis (Code-based)
2. Workout Focus Determination (LLM-assisted)  
3. Exercise Filtering (Code-based)
4. Workout Creation (LLM-creative)
5. Set Programming (Code-based)
"""

from .multi_phase_orchestrator import create_multi_phase_workout

__all__ = ["create_multi_phase_workout"]