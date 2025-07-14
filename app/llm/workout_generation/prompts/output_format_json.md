# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be a single, valid JSON object and nothing else. The content must be in **GERMAN**, though exercise names can be in English.

## Exaktes JSON-Ausgabeformat
Gib das Workout in folgendem JSON-Format zurück. Halte dich exakt an die Struktur und die Feldnamen.

- **`sets` object**: `{{"r": reps, "w": weight_kg, "s": duration_s, "d": distance_m, "p": pause_s}}`
- Use `null` for values that are not applicable.
- Do not include units in the JSON output.

```json
{{
  "muscle_group_load": [
    "Beine: Benötigen aktive Regeneration oder komplette Pause.",
    "Rücken/Bizeps (Pull): Leicht ermüdet (48h Erholung).",
    "Brust/Schultern/Trizeps (Push): Vollständig erholt.",
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
          ],
          "superset_group": null
        }},
        {{
          "name": "Arm Circles",
          "sets": [
            {{"r": 15}}
          ],
          "superset_group": null
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
          ],
          "superset_group": null
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
          ],
          "superset_group": null
        }}
      ]
    }}
  ]
}}
```

Beispiel-Parameter für `sets`