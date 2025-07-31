# Workout Generation V1 - Directory Structure and Usage Guide

## Overview

This directory contains the LLM-based workout generation system with support for multiple implementation versions. The structure allows for easy iteration and testing of different GenAI approaches while maintaining shared utilities.

## Directory Structure

```
workout_generation_v1/
├── shared/                      # Shared utilities across all versions
│   ├── formatting/             # Data formatting for LLM input
│   │   ├── training_history.py # Format user's training history
│   │   └── training_plan.py    # Format training plans
│   ├── parsing/                # Parse LLM output to DB models
│   │   ├── workout_parser.py   # Main parser for workout structure
│   │   └── workout_utils.py    # Utility functions for parsing
│   ├── prompt_utils/           # Prompt preparation utilities
│   │   ├── prepare_prompt.py   # Standard prompt preparation
│   │   └── prepare_prompt_versioned.py # Version-specific preparation
│   └── prompts/                # Shared prompt templates
│       ├── default_exercises.md
│       ├── equipment_matching_prompt.md
│       └── training_principles_base.md
│
├── versions/                    # Version-specific implementations
│   ├── standard/               # Full-featured workout generation
│   │   ├── llm_call.py        # LLM interaction logic
│   │   ├── schemas.py         # Pydantic schemas (CompactWorkoutSchema)
│   │   ├── service.py         # Main service entry point
│   │   ├── chain.py           # Workflow orchestration
│   │   └── prompts/           # Version-specific prompts
│   │       ├── workout_generation_prompt_base.md
│   │       ├── output_format_json.md
│   │       └── workout_generation_prompt_step1.md
│   │
│   └── minimal/                # Performance-optimized minimal version
│       ├── llm_call.py        # Simplified LLM call
│       ├── schemas.py         # Minimal schemas (MinimalWorkoutSchema)
│       ├── service.py         # Minimal service implementation
│       ├── chain.py           # Simplified workflow
│       └── prompts/           # Minimal prompts
│           ├── workout_generation_prompt_minimal.md
│           └── output_format_freeform.md
│
├── testing/                     # Testing and development files
│   ├── local_test_files/       # Test input/output files
│   ├── output/                 # Generated output samples
│   └── visualization/          # Workout visualization tools
│
└── __init__.py                 # Main module entry point
```

## Version Access Strategy

### 1. Standard Version (Full-Featured)
The standard version provides comprehensive workout generation with detailed structure, muscle group analysis, and training principles.

```python
# Import from the main module
from app.llm.workout_generation_v1 import create_workout_service, CompactWorkoutSchema

# Or import directly from the version
from app.llm.workout_generation_v1.versions.standard import (
    create_workout_service,
    CompactWorkoutSchema
)

# Usage
workout = await create_workout_service(
    user_profile=user_profile,
    training_history=training_history,
    training_goals=training_goals,
    training_plan=training_plan
)
```

**Features:**
- Detailed workout structure with blocks (Warm-up, Main, Cool-down)
- Comprehensive exercise parameters (reps, weight, duration, distance, pause)
- Muscle group load analysis
- Focus derivation based on training history
- Superset support

### 2. Minimal Version (Performance-Optimized)
The minimal version focuses on speed and simplicity, ideal for quick workout generation or testing.

```python
# Import from the main module
from app.llm.workout_generation_v1 import (
    workout_generation_service_minimal,
    MinimalWorkoutSchema
)

# Or import directly from the version
from app.llm.workout_generation_v1.versions.minimal import (
    workout_generation_service_minimal,
    MinimalWorkoutSchema
)

# Usage
workout = await workout_generation_service_minimal(
    user_profile=user_profile,
    training_history=training_history,
    training_goals=training_goals,
    training_plan=training_plan
)
```

**Features:**
- Simplified workout structure
- Basic exercise information (name and set count only)
- Faster generation time
- Lower token usage

## Adding New Versions

To add a new version:

1. Create a new directory under `versions/` (e.g., `versions/advanced/`)
2. Include the required files:
   - `__init__.py` - Package initialization
   - `service.py` - Main service entry point
   - `schemas.py` - Pydantic schemas (if different from existing)
   - `llm_call.py` - LLM interaction (can reuse existing)
   - `chain.py` - Workflow logic (optional if simple)
   - `prompts/` - Version-specific prompts

3. Update the main `__init__.py` to expose the new version:
```python
from .versions.advanced import advanced_workout_service
```

## Shared Utilities

### Formatting (`shared/formatting/`)
- `format_training_history_for_llm()` - Converts training history to LLM-friendly format
- `format_training_plan_for_llm()` - Formats training plans for LLM context

### Parsing (`shared/parsing/`)
- `workout_parser` - Parses LLM output to database models
- `workout_utils` - Helper functions for workout manipulation

### Prompt Utilities (`shared/prompt_utils/`)
- `prepare_prompt()` - Standard prompt preparation
- `prepare_prompt_versioned()` - Version-aware prompt preparation

## Development and Testing

The `testing/` directory contains:
- Sample inputs and outputs for testing
- Visualization tools for workout inspection
- Test data for different scenarios

To test a new version:
1. Use files in `testing/local_test_files/` as input
2. Compare output with samples in `testing/output/`
3. Use `testing/visualization/workout_viewer.html` to visualize results

## Best Practices

1. **Version Independence**: Each version should be self-contained
2. **Shared Code**: Use `shared/` for common functionality
3. **Prompt Management**: Keep prompts as separate markdown files
4. **Schema Evolution**: New schemas should extend or simplify existing ones
5. **Testing**: Always test with sample data before deployment