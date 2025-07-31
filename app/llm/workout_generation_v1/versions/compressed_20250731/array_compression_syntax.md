# Array-Based Compression Syntax for Workout Generation

## Core Concept: Position-Based Arrays

All exercise parameters are stored in arrays where the **position index determines the set number**. This maintains full flexibility while drastically reducing token usage.

## Basic Syntax

### Simple Exercise Structure
```json
{
  "name": "Pull-up",
  "reps": [7, 7, 6, 6],        // 4 sets with different reps
  "weight": null,              // Bodyweight exercise
  "rest": 120                  // Same rest for all sets
}
```

### Exercise with Varying Parameters
```json
{
  "name": "Barbell Bent Over Row",
  "reps": [12, 10, 8, 8],      // Warmup set + 3 working sets
  "weight": [40, 72.5, 72.5, 72.5],  // Different weight for warmup
  "rest": [60, 90, 90, 90]     // Different rest after warmup
}
```

### Time-Based Exercise
```json
{
  "name": "Plank Hold",
  "duration": [60, 60, 60],    // 3 sets of 60 seconds
  "rest": 60                   // Same rest for all
}
```

### Distance-Based Exercise
```json
{
  "name": "Farmer's Walk",
  "distance": [40, 40, 30],    // Meters
  "weight": 24,               // Using available 24kg KB
  "rest": [90, 90, 120]       // Longer rest after last set
}
```

## Advanced Features

### Supersets
```json
{
  "superset": "A",
  "exercises": [
    {
      "name": "Single-Arm Dumbbell Row (R)",
      "reps": [10, 10, 10],
      "weight": 32.5,
      "rest": 0  // No rest between superset exercises
    },
    {
      "name": "Single-Arm Dumbbell Row (L)",
      "reps": [10, 10, 10],
      "weight": 32.5,
      "rest": 60  // Rest after completing both sides
    }
  ]
}
```

### Equipment Constraints
```json
{
  "name": "Russian Kettlebell Swing",
  "reps": [20, 15, 15, 12],
  "weight": 24,  // Only available KB weight
  "rest": 60,
  "equipment_note": "24kg KB only"
}
```

### Mixed Parameter Types
```json
{
  "name": "AMRAP Circuit",
  "duration": [300],  // 5 minutes
  "target_rounds": 5,
  "exercises_within": ["10 KB Swings", "5 Pull-ups", "15 Push-ups"]
}
```

## Full Workout Example

```json
{
  "name": "Kraftaufbau Pull-Workout für funktionelle Stärke",
  "focus": "Kraft, Muskelaufbau, Funktionelle Stärke",
  "equipment": "24kg KB, Pull-up bar, Resistance band",
  "blocks": [
    {
      "name": "Warm-Up",
      "exercises": [
        {
          "name": "Arm Circles",
          "reps": [15, 15]
        },
        {
          "name": "Shoulder Pass-Through with Resistance Band",
          "reps": [12, 12]
        },
        {
          "name": "Band Pull-Aparts",
          "reps": [15, 15]
        }
      ]
    },
    {
      "name": "Main",
      "exercises": [
        {
          "name": "Pull-up",
          "reps": [7, 7, 6, 6],
          "rest": 120
        },
        {
          "name": "Barbell Bent Over Row",
          "reps": [8, 8, 8, 8],
          "weight": 72.5,
          "rest": 90
        },
        {
          "superset": "A",
          "exercises": [
            {
              "name": "Single-Arm Dumbbell Row (R)",
              "reps": [10, 10, 10],
              "weight": 32.5,
              "rest": 0
            },
            {
              "name": "Single-Arm Dumbbell Row (L)",
              "reps": [10, 10, 10],
              "weight": 32.5,
              "rest": 60
            }
          ]
        },
        {
          "name": "Face Pull",
          "reps": [12, 12, 12],
          "weight": 25,
          "rest": 60
        },
        {
          "name": "Barbell Curl",
          "reps": [10, 10, 10],
          "weight": 40,
          "rest": 60
        },
        {
          "name": "Hammer Curl with Dumbbells",
          "reps": [12, 12, 12],
          "weight": 12,
          "rest": 60
        },
        {
          "name": "Plank Hold",
          "duration": [60, 60, 60],
          "rest": 60
        },
        {
          "name": "Russian Twist",
          "reps": [20, 20, 20],
          "rest": 60
        }
      ]
    },
    {
      "name": "Cool-Down",
      "exercises": [
        {
          "name": "Child's Pose",
          "duration": [60]
        },
        {
          "name": "Cat-Cow Flow",
          "reps": [10]
        }
      ]
    }
  ]
}
```

## Compression Benefits

### Token Comparison
- **Original format**: ~8,500 tokens (431 lines)
- **Array format**: ~800 tokens (60-70 lines)
- **Reduction**: ~90% fewer tokens

### Maintained Flexibility
- ✅ Individual set variations (reps, weight, rest)
- ✅ Warmup sets with different parameters
- ✅ Superset structures
- ✅ Equipment constraints
- ✅ Mixed exercise types (reps/time/distance)

## Edge Cases & Special Notations

### Drop Sets
```json
{
  "name": "Lateral Raise Drop Set",
  "reps": [12, 10, 15],
  "weight": [10, 7.5, 5],
  "rest": [0, 0, 90],
  "note": "drop"
}
```

### Rest-Pause Sets
```json
{
  "name": "Barbell Curl Rest-Pause",
  "reps": [10, 5, 3],
  "weight": 40,
  "rest": [15, 15, 60],
  "note": "rest-pause"
}
```

### Pyramid Sets
```json
{
  "name": "Dumbbell Press Pyramid",
  "reps": [12, 10, 8, 10, 12],
  "weight": [20, 25, 30, 25, 20],
  "rest": 60
}
```

## Questions for Consideration

1. **Default Values**: Should we assume certain defaults?
   - If `rest` is not specified, assume 60s?
   - If `weight` is not specified for non-bodyweight exercises, flag for user input?

2. **Notation Shortcuts**: Should we support even more compressed notations?
   - `"reps": "3x10"` when all sets are identical?
   - `"reps": "12-10-8"` for simple progressions?

3. **Equipment Handling**: How to handle equipment variations?
   - Should we include `equipment_type` field?
   - Example: `"equipment_type": "KB"` vs `"equipment_type": "DB"`

4. **Complex Movements**: How to handle exercises with multiple components?
   - Clean & Press: Two movements, one exercise?
   - 21s (7-7-7 rep scheme with partials)?

5. **Intensity Techniques**: Should we add a `technique` field?
   - `"technique": "tempo"` with `"tempo": [3, 1, 1, 0]`?
   - `"technique": "cluster"` for cluster sets?

## Post-Processing Example

```python
def expand_exercise(exercise):
    """Expand compressed exercise format to full structure"""
    
    # Determine number of sets
    num_sets = len(exercise.get('reps', [])) or \
               len(exercise.get('duration', [])) or \
               len(exercise.get('distance', []))
    
    # Expand single values to arrays
    if isinstance(exercise.get('weight'), (int, float)):
        exercise['weight'] = [exercise['weight']] * num_sets
    
    if isinstance(exercise.get('rest'), (int, float)):
        exercise['rest'] = [exercise['rest']] * num_sets
    
    # Create full set objects
    sets = []
    for i in range(num_sets):
        set_obj = {
            'position': i,
            'reps': exercise['reps'][i] if 'reps' in exercise else None,
            'weight': exercise['weight'][i] if 'weight' in exercise else None,
            'duration': exercise['duration'][i] if 'duration' in exercise else None,
            'distance': exercise['distance'][i] if 'distance' in exercise else None,
            'rest_time': exercise['rest'][i] if 'rest' in exercise else None
        }
        sets.append(set_obj)
    
    return sets
```

## Conclusion

This array-based compression syntax achieves:
- **90% token reduction** while maintaining full flexibility
- **Intuitive structure** where position = set number
- **Equipment awareness** with explicit weight constraints
- **Support for all exercise types** and training techniques

The format is both human-readable and LLM-friendly, making it ideal for fast, intelligent workout generation.