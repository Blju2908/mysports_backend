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
[{'type': 'text', 'text': 'Workout: Hyrox Hybrid Strength & Endurance (≈60 min | Fokus: Hyrox, Kraft, Ausdauer)\n\nWarm-Up | 7 min | Mobilisierung & Aktivierung\n- Jumping Jacks | –\n    - 60 s\n- Butt Kicks | –\n    - 60 s\n- Armkreisen | –\n    - 10 reps\n- Air Squat | –\n    - 15 reps\n- Inchworm Walkout | –\n    - 5 reps\n\nMain | 45 min | Kraft & Hyrox Zirkel\n- Front Squat mit Langhantel | –\n    - 6 @ 60 kg / P: 90 s\n    - 6 @ 80 kg / P: 90 s\n    - 5 @ 85 kg / P: 120 s\n    - 4 @ 90 kg / P: 120 s\n- Striktes Schulterdrücken mit Langhantel | –\n    - 8 @ 40 kg / P: 90 s\n    - 6 @ 50 kg / P: 90 s\n    - 5 @ 55 kg / P: 90 s\n- Ski Ergometer | A\n    - 250 m / P: 60 s\n    - 250 m / P: 60 s\n    - 250 m / P: 60 s\n- Wall Ball Shot | A\n    - 15 reps / P: 60 s\n    - 15 reps / P: 60 s\n    - 15 reps / P: 60 s\n- Sled Push | A\n    - 20 m / P: 60 s\n    - 20 m / P: 60 s\n    - 20 m / P: 60 s\n- Farmers Walk mit Kurzhanteln | A\n    - 50 m @ 22,5 kg / P: 60 s\n    - 50 m @ 22,5 kg / P: 60 s\n    - 50 m @ 22,5 kg / P: 60 s\n- Burpee Broad Jump | A\n    - 5 reps / P: 60 s\n    - 5 reps / P: 60 s\n    - 5 reps / P: 60 s\n\nCool-Down | 8 min | Dehnung & Mobilität\n- Downward Dog to Cobra | –\n    - 60 s\n- Butterfly Stretch | –\n    - 60 s\n- Figure-4-Dehnung im Sitzen links | C\n    - 30 s\n- Figure-4-Dehnung im Sitzen rechts | C\n    - 30 s\n- Happy Baby Pose | –\n    - 60 s\n- Cat-Cow Flow | –\n    - 60 s', 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 