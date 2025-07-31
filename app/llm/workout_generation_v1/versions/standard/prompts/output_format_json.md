# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be a single, valid JSON object and nothing else. The content must be in **GERMAN**, though exercise names can be in English.

## Exaktes JSON-Ausgabeformat
Gib das Workout in folgendem JSON-Format zurück. Halte dich exakt an die Struktur und die Feldnamen.

- **`sets` object**: `{{"r": reps, "w": weight_kg, "s": duration_s, "d": distance_m, "p": pause_s}}`
- **Omit fields that are not applicable.**
- **Omit Nulls**: Do not include fields with `null` values in the JSON output. This applies especially to `sets` objects (e.g., if reps are not applicable, omit the `r` field instead of setting `r: null`).
- Do not include units in the JSON output.

```json
{{
  "muscle_group_load": [
    "Beine: Benötigen aktive Regeneration oder komplette Pause.",
    "Rücken/Bizeps (Pull): Stark ermüdet nach gestrigem Training. Pause empfohlen.",
    "Brust/Schultern/Trizeps (Push): Trotz gestriger Belastung leicht ermüdet. Nicht alle Bereiche der Muskelgruppe wurden beansprucht. Daher Push Workout möglich. ",
    "Core: Vollständig erholt."
  ],
  "focus_derivation": "Heutiger Fokus: Oberkörper (Kraft) und Rumpfstabität. Begründung: Um den Beinen nach der gestrigen, langen Radtour ausreichend Erholungszeit zu geben (>48h), ist ein Oberkörper-Workout ideal.",
  "name": "Intensives Oberkörper-Workout",
  "duration_min": 60,
  "focus": "Kraft, Muskelaufbau",
  "description": "Ein anspruchsvolles Oberkörper-Workout, das auf Kraft und Hypertrophie mit einer Mischung aus Grund- und Isolationsübungen abzielt.",
  "blocks": [
    {{
      "name": "Warm-Up",
      "duration_min": 5,
      "description": "Allgemeine Erwärmung und Aktivierung",
      "exercises": [
        {{
          "name": "Jumping Jacks",
          "sets": [
            {{"s": 60}}
          ]
        }},
        {{
          "name": "Arm Circles",
          "sets": [
            {{"r": 15}}
          ]
        }}
      ]
    }},
    {{
      "name": "Main",
      "duration_min": 50,
      "description": "Hauptteil mit Fokus auf Push & Pull",
      "exercises": [
        {{
          "name": "Barbell Bench Press",
          "sets": [
            {{"r": 8, "w": 80.0, "p": 120}},
            {{"r": 8, "w": 80.0, "p": 120}},
            {{"r": 6, "w": 82.5, "p": 120}}
          ]
        }},
        {{
          "name": "Single-Arm Dumbbell Row (rechts)",
          "sets": [
            {{"r": 10, "w": 30.0, "p": 0}},
            {{"r": 10, "w": 30.0, "p": 0}},
            {{"r": 10, "w": 30.0, "p": 60}}
          ],
          "superset_group": "A"
        }},
        {{
          "name": "Single-Arm Dumbbell Row (links)",
          "sets": [
            {{"r": 10, "w": 30.0, "p": 0}},
            {{"r": 10, "w": 30.0, "p": 0}},
            {{"r": 10, "w": 30.0, "p": 60}}
          ],
          "superset_group": "A"
        }}
      ]
    }},
    {{
      "name": "Cool-Down",
      "duration_min": 5,
      "description": "Dehnung der beanspruchten Muskulatur",
      "exercises": [
        {{
          "name": "Doorway Pec Stretch",
          "sets": [
            {{"s": 30}}
          ]
        }}
      ]
    }}
  ]
}}
```