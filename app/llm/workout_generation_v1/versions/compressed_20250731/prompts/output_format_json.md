# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be a single, valid JSON object and nothing else. The content must be in **GERMAN**, though exercise names can be in English.

## Array-Based Compressed JSON Format

Use arrays where the **position index = set number**. This drastically reduces tokens while maintaining full flexibility.

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
  "muscle_group_load": [
    "Beine: Stark ermüdet nach gestrigem Lauf. Benötigen Regeneration.",
    "Rücken/Bizeps (Pull): Vollständig erholt und bereit für intensive Belastung.",
    "Brust/Schultern/Trizeps (Push): Leicht ermüdet. Vordere Schulter schonen.",
    "Core: Vollständig erholt."
  ],
  "focus_derivation": "Heutiger Fokus: Rücken, Bizeps und Rumpf. Begründung: Um den Beinen ausreichend Erholungszeit zu geben, konzentriert sich das Training auf die erholten Zugmuskeln.",
  "name": "Kraftaufbau Pull-Workout für funktionelle Stärke",
  "duration_min": 60,
  "focus": "Kraft, Muskelaufbau, Funktionelle Stärke",
  "description": "Ein fokussiertes Pull-Workout zur Steigerung der Kraft im Rücken und Bizeps.",
  "blocks": [
    {
      "name": "Warm-Up",
      "duration_min": 5,
      "description": "Allgemeine Erwärmung und Aktivierung",
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
      "description": "Hauptteil mit Fokus auf Kraft und Muskelaufbau",
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
      "description": "Dehnung der beanspruchten Muskulatur",
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
1. **Omit null/empty fields** - Don't include fields that aren't applicable
2. **Use arrays for varying parameters** - Position in array = set number
3. **Single values when uniform** - Use single value for weight/rest if same for all sets
4. **Equipment constraints** - Respect available equipment weights (e.g., only 24kg KB)
5. **German content** - All descriptions in German, exercise names can be English