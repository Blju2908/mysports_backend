# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be a single, valid JSON object and nothing else. The content must be in **GERMAN**, though exercise names can be in English.

## Array-Based Compressed JSON Format

Use arrays where the **position index = set number**. This drastically reduces tokens while maintaining full flexibility.

**CRITICAL**: All arrays for an exercise MUST have the same length!
- If an exercise has 4 sets, then `reps`, `weight`, `tags`, and `rest` (if arrays) must ALL have 4 elements
- Use `null` for non-applicable values (e.g., `tags = [null, null, null, null]` if no tags needed)

### Basic Exercise Structure
```json
{
  "name": "Pull-up",
  "reps": [7, 7, 6, 6],      // 4 sets
  "rest": 120                // Same rest for all sets
}
```

### Exercise with Varying Parameters
```json
{
  "name": "Barbell Bent Over Row",
  "reps": [12, 10, 8, 8],    // Warmup + 3 working sets
  "weight": [40, 72.5, 72.5, 72.5],  // Different weight for warmup
  "rest": [60, 90, 90, 90]   // Different rest after warmup
}
```

### Exercise with Warm-up Tag
```json
{
  "name": "Deadlift",
  "reps": [8, 5, 5, 5, 3],
  "weight": [60, 100, 120, 120, 140],
  "tags": ["warm_up", "warm_up", null, null, null],  // First 2 sets are warm-up
  "rest": [60, 90, 120, 120, 180]
}
```

### Time-Based Exercise
```json
{
  "name": "Plank Hold",
  "duration": [60, 60, 60],  // 3 sets of 60 seconds
  "rest": 60
}
```

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

## Complete Example Output

```json
{
  "focus_derivation": "Fokus auf Rücken und Bizeps, da Beine nach gestrigem Lauf Regeneration benötigen.",
  "name": "Kraftaufbau Pull-Workout für funktionelle Stärke",
  "duration_min": 60,
  "focus": "Kraft, Muskelaufbau, Funktionelle Stärke",
  "description": "Pull-Workout für Kraft und Muskelaufbau.",
  "blocks": [
    {
      "name": "Warm-Up",
      "duration_min": 5,
      "exercises": [
        {
          "name": "Arm Circles",
          "reps": [15, 15]
        },
        {
          "name": "Band Pull-Aparts",
          "reps": [15, 15]
        }
      ]
    },
    {
      "name": "Main",
      "duration_min": 50,
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
          "name": "Plank Hold",
          "duration": [60, 60, 60],
          "rest": 60
        }
      ]
    },
    {
      "name": "Cool-Down",
      "duration_min": 5,
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

## Important Rules:
1. **Array Length Consistency** - ALL arrays for an exercise MUST have the same length (number of sets)
2. **Omit null/empty fields** - Don't include fields that aren't applicable (but within arrays, use null)
3. **Use arrays for varying parameters** - Position in array = set number
4. **Single values when uniform** - Use single value for weight/rest if same for all sets
5. **Equipment constraints** - Respect available equipment weights (e.g., only 24kg KB)
6. **German content** - All descriptions in German, exercise names can be English
7. **Warm-up sets** - Use `tags: ["warm_up", ...]` for warm-up sets with lower weight/higher reps