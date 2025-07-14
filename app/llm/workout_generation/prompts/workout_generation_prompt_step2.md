# Task
Convert the following freeform workout text into the exact JSON schema format. You are a data parser.

# Rules
1.  **Precise Structuring**: Extract all information and map it correctly.
2.  **Schema Conformance**: Strictly follow the WorkoutSchema (name, description, duration, focus, blocks).
3.  **Set Parameters**: For each set: [weight_kg, repetitions, duration_sec, distance_m, rest_sec] - use `null` for irrelevant values. Ensure parameters are placed correctly!!!
4.  **Superset IDs**: Retain the same IDs (A, B, C) for grouped exercises.
5.  **Realistic Values**: Preserve all weights, times, and repetitions.
6.  **No Null Bytes**: Never use null bytes or other invalid characters.
7.  **Completeness**: Always output the entire workout!

Parameter Notation of Input:
-   Weight + Repetitions: `8 @ 80 kg / P: 60 s`
-   Repetitions: `15 reps`
-   Duration: `60 s`
-   Duration and Weight: `60 s @ 80 kg`
-   Distance: `300 m`
-   Rest: `... / P: 60 s` --> Rest in seconds

# Full Workout Example
For a workout with Warm-Up, Main, and Cooldown:
```json
{{
  "name": "Krafttraining Oberkörper",
  "description": "Vollständiges Krafttraining für den Oberkörper mit Warm-Up und Cooldown",
  "duration": 60,
  "focus": "Kraft, Oberkörper",
  "blocks": [
    {{
      "name": "Warm-Up",
      "description": "Dynamische Aufwärmung",
      "exercises": [
        {{
          "name": "Jumping Jacks",
          "sets": [
            {{"values": [null, null, 60, null, null]}}
          ]
        }},
        {{
          "name": "Armkreisen",
          "sets": [
            {{"values": [null, 10, null, null, null]}}
          ]
        }}
      ]
    }},
    {{
      "name": "Hauptteil",
      "description": "Krafttraining Superset",
      "exercises": [
        {{
          "name": "Kurzhantel Bankdrücken",
          "superset_id": "A",
          "sets": [
            {{"values": [20, 12, null, null, 60]}},
            {{"values": [20, 10, null, null, 60]}},
            {{"values": [20, 8, null, null, 60]}}
          ]
        }},
        {{
          "name": "Kurzhantel Rudern",
          "superset_id": "A",
          "sets": [
            {{"values": [20, 12, null, null, 0]}},
            {{"values": [20, 10, null, null, 0]}},
            {{"values": [20, 8, null, null, 0]}}
          ]
        }}
      ]
    }},
    {{
      "name": "Cooldown",
      "description": "Dehnung und Entspannung",
      "exercises": [
        {{
          "name": "Brustdehnung",
          "sets": [
            {{"values": [null, null, 30, null, null]}}
          ]
        }}
      ]
    }}
  ]
}}
```

# Input
{FREEFORM_WORKOUT_PLACEHOLDER}

# Output
Strictly correct JSON without Markdown or additional explanations. The output MUST be in GERMAN. 