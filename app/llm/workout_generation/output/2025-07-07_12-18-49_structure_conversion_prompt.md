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
[{'type': 'text', 'text': "Workout: Leg Day & Core (≈60 min | Fokus: Beine, Gesäß, Core)\n\nWarm-Up | 10 min | Mobilisation & leichtes Cardio\n- Assault Bike | –\n    - 300 s\n- Hip Circles | –\n    - 10 reps / P: 0 s\n- World's Greatest Hip Opener | –\n    - 30 s / P: 0 s\n    - 30 s / P: 0 s\n- Inchworm Walkout | –\n    - 8 reps / P: 0 s\n- Leg Swings Front-to-Back links | A\n    - 10 reps / P: 0 s\n- Leg Swings Front-to-Back rechts | A\n    - 10 reps / P: 0 s\n\nMain | 45 min | Kraft & Hypertrophie Beine + Core\n- Smith Machine Box Squat | –\n    - 8 reps @ 100 kg / P: 90 s\n    - 8 reps @ 100 kg / P: 90 s\n    - 8 reps @ 100 kg / P: 90 s\n    - 8 reps @ 100 kg / P: 90 s\n- Barbell Romanian Deadlift | –\n    - 8 reps @ 80 kg / P: 90 s\n    - 8 reps @ 80 kg / P: 90 s\n    - 8 reps @ 80 kg / P: 90 s\n- Bulgarian Split Squat with Dumbbells links | B\n    - 8 reps @ 24 kg / P: 90 s\n    - 8 reps @ 24 kg / P: 90 s\n    - 8 reps @ 24 kg / P: 90 s\n- Bulgarian Split Squat with Dumbbells rechts | B\n    - 8 reps @ 24 kg / P: 90 s\n    - 8 reps @ 24 kg / P: 90 s\n    - 8 reps @ 24 kg / P: 90 s\n- Barbell Hip Thrust | –\n    - 10 reps @ 70 kg / P: 90 s\n    - 10 reps @ 70 kg / P: 90 s\n    - 10 reps @ 70 kg / P: 90 s\n- Plank Hold | C\n    - 45 s / P: 30 s\n    - 45 s / P: 30 s\n    - 45 s / P: 30 s\n- Reverse Crunch | C\n    - 15 reps / P: 30 s\n    - 15 reps / P: 30 s\n    - 15 reps / P: 30 s\n\nCool-Down | 5 min | Dehnung & Mobilität\n- 90/90 Hip Switch | –\n    - 60 s\n- Kneeling Quad Stretch links | D\n    - 45 s\n- Kneeling Quad Stretch rechts | D\n    - 45 s\n- Child's Pose | –\n    - 90 s", 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 