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
[{'type': 'text', 'text': "Workout: Push Kraft & Hypertrophie (≈60 min | Fokus: Brust, Schultern, Trizeps)\n\nWarm-Up | 10 Minuten | Mobilisation & Aktivierung Oberkörper\n- Arm Circles | –\n    - 15 reps\n- Shoulder Pass-Through with Resistance Band | –\n    - 12 reps\n- Inchworm Walkout | –\n    - 8 reps\n\nMain | 45 Minuten | Kraft & Muskelaufbau Push\n- Barbell Bench Press | –\n    - 6 @ 80 kg / P: 120 s\n    - 6 @ 80 kg / P: 120 s\n    - 6 @ 80 kg / P: 120 s\n    - 6 @ 80 kg / P: 120 s\n- Dumbbell Incline Bench Press | –\n    - 8 @ 30 kg / P: 90 s\n    - 8 @ 30 kg / P: 90 s\n    - 8 @ 30 kg / P: 90 s\n- Strict Barbell Overhead Press | –\n    - 6 @ 50 kg / P: 120 s\n    - 6 @ 50 kg / P: 120 s\n    - 6 @ 50 kg / P: 120 s\n    - 6 @ 50 kg / P: 120 s\n- Bench Dip Feet Elevated | A\n    - 10 @ 10 kg / P: 60 s\n    - 10 @ 10 kg / P: 60 s\n    - 10 @ 10 kg / P: 60 s\n- Lateral Raise with Dumbbells | A\n    - 12 @ 10 kg / P: 60 s\n    - 12 @ 10 kg / P: 60 s\n    - 12 @ 10 kg / P: 60 s\n- Cable Triceps Push-down with Rope | –\n    - 12 @ 30 kg / P: 60 s\n    - 12 @ 30 kg / P: 60 s\n    - 12 @ 30 kg / P: 60 s\n\nCool-Down | 5 Minuten | Dehnung & Entspannung Oberkörper\n- Doorway Pec Stretch | –\n    - 30 s\n- Triceps Overhead Stretch links | –\n    - 30 s\n- Triceps Overhead Stretch rechts | –\n    - 30 s\n- Child's Pose | –\n    - 60 s", 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 