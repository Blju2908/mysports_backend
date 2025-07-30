# Exercise Description Enhancement System

This system enhances existing exercise descriptions with new fields for muscle fatigue calculation, volume calculation, and advanced filtering.

## Overview

The enhancement system consists of several components:

1. **Download**: Extract existing exercise descriptions from database
2. **Enhancement**: Use OpenAI LLM to add new metadata fields
3. **Upload**: Save enhanced descriptions back to database
4. **Scripts**: Easy-to-use command-line scripts for each step

## New Fields Added

### Muscle Group Mapping (for fatigue calculation)
- `primary_muscle_groups`: Main muscles (100% fatigue impact)
- `secondary_muscle_groups`: Supporting muscles (30-50% fatigue impact)  
- `muscle_activation_coefficients`: Fatigue coefficients per muscle (0.1-1.0)
- `base_fatigue_factor`: Base fatigue multiplier (0.5-2.0)

### Exercise Classification (for volume calculation)
- `exercise_type`: strength|cardio|flexibility|plyometric|isometric
- `metabolic_demand`: low|moderate|high|very_high
- `volume_calculation_type`: weight_based|time_based|bodyweight_based|distance_based

### Movement Characteristics
- `movement_category`: compound|isolation|functional|corrective
- `movement_plane`: Array of sagittal|frontal|transverse
- `intensity_level`: low|moderate|high|maximal
- `recommended_recovery_hours`: Minimum recovery time

### Equipment & Space
- `required_equipment`: Specific equipment needed
- `equipment_alternatives`: Alternative equipment options
- `space_requirements`: minimal|small|medium|large|outdoor

### Workout Programming
- `superset_compatible_with`: Compatible movement patterns
- `antagonist_patterns`: Opposing movement patterns
- `progression_method`: load|reps|time|difficulty|range_of_motion
- `beginner_starting_point`: Default parameters for beginners

### Safety & Prerequisites
- `injury_considerations`: Contraindications and risks
- `prerequisite_movements`: Required preparatory exercises

## Usage

### 1. Download Exercise Descriptions

```bash
cd backend
python scripts/download_exercise_descriptions.py
```

This downloads all current exercise descriptions from the database and saves them to a timestamped JSON file.

### 2. Enhance Exercise Descriptions

```bash
cd backend
python scripts/enhance_exercise_descriptions.py
```

This runs the complete enhancement workflow:
- Downloads exercises from database (or uses existing file)
- Processes them in batches through OpenAI LLM
- Saves enhanced descriptions to JSON file

**Configuration:**
- Batch size: 5 exercises per LLM call (recommended for complex enhancement)
- Delay: 3 seconds between batches (to avoid rate limits)
- Uses OpenAI o4-mini model with structured output

### 3. Upload Enhanced Descriptions

```bash
cd backend
python scripts/upload_enhanced_exercises.py
```

This uploads the enhanced exercise descriptions back to the database, updating existing records with new fields.

## File Structure

```
backend/app/llm/exercise_description/
├── download_exercises.py              # Download from database
├── enhanced_exercise_schemas.py       # New schema definitions
├── exercise_enhancement_prompt.md     # LLM prompt template
├── enhance_exercises_chain.py         # LLM enhancement logic
├── upload_enhanced_exercises.py       # Upload to database
├── enhance_exercises_main.py          # Main enhancement workflow
└── output/                           # Generated files
    ├── exercise_descriptions_download_*.json
    └── exercise_descriptions_enhanced_*.json

backend/scripts/
├── download_exercise_descriptions.py  # Script: Download
├── enhance_exercise_descriptions.py   # Script: Enhance
└── upload_enhanced_exercises.py      # Script: Upload
```

## Example Enhanced Exercise

```json
{
  "name_german": "Bankdrücken",
  "name_english": "Bench Press",
  "primary_muscle_groups": ["Brust", "Vordere Schulter", "Trizeps"],
  "secondary_muscle_groups": ["Rumpfstabilität"],
  "muscle_activation_coefficients": {
    "Brust": 1.0,
    "Vordere Schulter": 0.7,
    "Trizeps": 0.8,
    "Rumpfstabilität": 0.3
  },
  "exercise_type": "strength",
  "metabolic_demand": "moderate",
  "movement_category": "compound",
  "volume_calculation_type": "weight_based",
  "progression_method": "load",
  "beginner_starting_point": {
    "reps": 10,
    "sets": 3,
    "weight_percentage": 60
  }
}
```

## Requirements

- OpenAI API key (set as `OPENAI_API_KEY2` environment variable)
- Langchain OpenAI integration
- Database access (Supabase configuration)

## Notes

- Enhancement uses OpenAI o4-mini with medium reasoning effort
- Processes exercises in small batches to ensure quality
- Maintains all original fields while adding new ones
- Safe: Downloads and saves incrementally, allowing for recovery
- Database model needs to be updated separately to include new fields

## Next Steps

After running the enhancement and upload:

1. **Update Database Model**: Add the new fields to `ExerciseDescription` model
2. **Create Migration**: Generate Alembic migration for new columns
3. **Update API**: Modify endpoints to use new fields
4. **Test Integration**: Verify new fields work with workout generation system