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
[{'type': 'text', 'text': "Workout: Strength & Aesthetics (≈60 min | Fokus: Kraft, Muskelaufbau)\n\nWarm-Up | 10 min | Mobilisation und Aktivierung\n- Arm Circles | –\n    - 15 reps / P: 0 s\n    - 15 reps / P: 0 s\n- Inchworm Walkout | –\n    - 6 reps / P: 0 s\n- Air Squat | –\n    - 12 reps / P: 0 s\n    - 12 reps / P: 0 s\n- Hip Circles | –\n    - 10 reps / P: 0 s\n    - 10 reps / P: 0 s\n\nMain | 45 min | Kraft & Hypertrophie\n- Back Squat | –\n    - 6 reps @ 100 kg / P: 120 s\n    - 6 reps @ 100 kg / P: 120 s\n    - 6 reps @ 100 kg / P: 120 s\n    - 6 reps @ 100 kg / P: 120 s\n- Barbell Bench Press | –\n    - 8 reps @ 80 kg / P: 120 s\n    - 8 reps @ 80 kg / P: 120 s\n    - 8 reps @ 80 kg / P: 120 s\n    - 8 reps @ 80 kg / P: 120 s\n- Pull-up | –\n    - 8 reps / P: 120 s\n    - 8 reps / P: 120 s\n    - 8 reps / P: 120 s\n    - 8 reps / P: 120 s\n- Arnold Press | –\n    - 8 reps @ 22.5 kg / P: 90 s\n    - 8 reps @ 22.5 kg / P: 90 s\n    - 8 reps @ 22.5 kg / P: 90 s\n    - 8 reps @ 22.5 kg / P: 90 s\n- Barbell Curl | C\n    - 10 reps @ 45 kg / P: 60 s\n    - 10 reps @ 45 kg / P: 60 s\n    - 10 reps @ 45 kg / P: 60 s\n    - 10 reps @ 45 kg / P: 60 s\n- Bench Dip Feet Elevated | C\n    - 12 reps / P: 60 s\n    - 12 reps / P: 60 s\n    - 12 reps / P: 60 s\n    - 12 reps / P: 60 s\n\nCool-Down | 5 min | Dehnung & Mobilität\n- Child's Pose | –\n    - 60 s\n- Downward Dog | –\n    - 60 s\n- Standing Quad Stretch links | D\n    - 30 s\n- Standing Quad Stretch rechts | D\n    - 30 s", 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 