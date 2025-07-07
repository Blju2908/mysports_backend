# Aufgabe
Konvertiere den folgenden freien Workout-Text in das exakte JSON-Schema-Format. Du bist ein Datenparser.

# Regeln
1. **Präzise Strukturierung**: Extrahiere alle Informationen und mappe sie korrekt
2. **Schema-Konformität**: Folge exakt dem WorkoutSchema (name, description, duration, focus, blocks)
3. **Set-Parameter**: Pro Satz: [Gewicht_kg, Wiederholungen, Dauer_sek, Distanz_m, Pause_sek] - nutze `null` für nicht relevante Werte. Achte darauf, dass die Parameter an den richtigen Stellen eingesetzt werden!!!
4. **Superset-IDs**: Übernehme gleiche IDs (A, B, C) für gruppierte Übungen
5. **Realistische Werte**: Behalte alle Gewichte, Zeiten und Wiederholungen bei
6. **Keine Null-Bytes**: Verwende niemals Null-Bytes oder andere ungültige Zeichen
7. **Vollständigkeit**: Gib immer das gesamte Workout aus!

Parameternotation des Inputs:
- Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
- Wiederholungen: `15 reps`
- Dauer: `60 s`
- Dauer und Gewicht: `60 s @ 80 kg`
- Distanz: `300 m`
- Pause: `... / P: 60 s` --> Pause in Sekunden


# Vollständiges Workout-Beispiel
Für ein Workout mit Warm-Up, Hauptteil und Cooldown:
```json
{
  "name": "Krafttraining Oberkörper",
  "description": "Vollständiges Krafttraining für den Oberkörper mit Warm-Up und Cooldown",
  "duration": 60,
  "focus": "Kraft, Oberkörper",
  "blocks": [
    {
      "name": "Warm-Up",
      "description": "Dynamische Aufwärmung",
      "exercises": [
        {
          "name": "Jumping Jacks",
          "sets": [
            {"values": [null, null, 60, null, null]}
          ]
        },
        {
          "name": "Armkreisen",
          "sets": [
            {"values": [null, 10, null, null, null]}
          ]
        }
      ]
    },
    {
      "name": "Hauptteil",
      "description": "Krafttraining Superset",
      "exercises": [
        {
          "name": "Kurzhantel Bankdrücken",
          "superset_id": "A",
          "sets": [
            {"values": [20, 12, null, null, 60]},
            {"values": [20, 10, null, null, 60]},
            {"values": [20, 8, null, null, 60]}
          ]
        },
        {
          "name": "Kurzhantel Rudern",
          "superset_id": "A",
          "sets": [
            {"values": [20, 12, null, null, 0]},
            {"values": [20, 10, null, null, 0]},
            {"values": [20, 8, null, null, 0]}
          ]
        }
      ]
    },
    {
      "name": "Cooldown",
      "description": "Dehnung und Entspannung",
      "exercises": [
        {
          "name": "Brustdehnung",
          "sets": [
            {"values": [null, null, 30, null, null]}
          ]
        }
      ]
    }
  ]
}
```

# Input
[{'type': 'text', 'text': "Workout: Lower Body Strength & Aesthetic (≈60 min | Fokus: Strength, Hypertrophy, Beine, Glutes)\n\nWarm-Up | 10 min | Mobilisation & Aktivierung\n- Ankle Bounces | –\n    - 20 reps\n- Hip Circles | –\n    - 10 reps\n- Air Squat | –\n    - 15 reps\n- Inchworm Walkout | –\n    - 8 reps\n- Glute Bridge | –\n    - 15 reps\n\nMain | 45 min | Kraft & Hypertrophie\n- Back Squat | –\n    - 6 @ 100 kg / P: 120 s\n    - 6 @ 100 kg / P: 120 s\n    - 6 @ 100 kg / P: 120 s\n    - 6 @ 100 kg / P: 120 s\n- Barbell Romanian Deadlift | –\n    - 8 @ 80 kg / P: 90 s\n    - 8 @ 80 kg / P: 90 s\n    - 8 @ 80 kg / P: 90 s\n- Bulgarian Split Squat left | A\n    - 8 @ 40 kg / P: 60 s\n    - 8 @ 40 kg / P: 60 s\n    - 8 @ 40 kg / P: 60 s\n- Bulgarian Split Squat right | A\n    - 8 @ 40 kg / P: 60 s\n    - 8 @ 40 kg / P: 60 s\n    - 8 @ 40 kg / P: 60 s\n- Barbell Hip Thrust | –\n    - 10 @ 80 kg / P: 90 s\n    - 10 @ 80 kg / P: 90 s\n    - 10 @ 80 kg / P: 90 s\n- Leg Press | –\n    - 12 @ 200 kg / P: 90 s\n    - 12 @ 200 kg / P: 90 s\n    - 12 @ 200 kg / P: 90 s\n- Calf Raise on Machine | –\n    - 15 @ 100 kg / P: 60 s\n    - 15 @ 100 kg / P: 60 s\n    - 15 @ 100 kg / P: 60 s\n\nCool-Down | 5 min | Flexibilität & Erholung\n- Hamstring Stretch (Standing) left | C\n    - 30 s\n- Hamstring Stretch (Standing) right | C\n    - 30 s\n- Hip Flexor Stretch (Kneeling) left | D\n    - 30 s\n- Hip Flexor Stretch (Kneeling) right | D\n    - 30 s\n- Child's Pose | –\n    - 60 s\n- Butterfly Stretch | –\n    - 60 s\n- Doorway Pec Stretch | –\n    - 60 s", 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 