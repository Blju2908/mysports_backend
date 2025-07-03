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
[{'type': 'text', 'text': 'Workout: Hyrox-Style Full-Body Strength & Endurance (≈60 min | Fokus: Kraft, Ausdauer, Funktional)\n\nWarm-Up | 8 min | Mobilität & Erwärmung\n- Jumping Jacks | –\n    - 60 s\n- Armkreisen | –\n    - 15 reps\n- Air Squat | –\n    - 15 reps\n- Inchworm Walkout | –\n    - 6 reps\n\nMain | 45 min | Kraftaufbau & Hyrox Circuit\n- Front Squat mit Langhantel | –\n    - 6 @ 85 kg / P: 90 s\n    - 6 @ 70 kg / P: 90 s\n    - 8 @ 60 kg / P: 90 s\n- Bankdrücken mit Langhantel | –\n    - 6 @ 70 kg / P: 90 s\n    - 8 @ 60 kg / P: 90 s\n    - 10 @ 50 kg / P: 90 s\n- Pull-up an der Klimmzugstange | –\n    - 8 reps / P: 60 s\n    - 8 reps / P: 60 s\n    - 8 reps / P: 60 s\n- Romanian Deadlift mit Langhantel | –\n    - 8 @ 80 kg / P: 90 s\n    - 10 @ 70 kg / P: 90 s\n    - 12 @ 60 kg / P: 90 s\n- Ski Ergometer | C\n    - 300 m / P: 0 s\n    - 300 m / P: 0 s\n    - 300 m / P: 0 s\n- Sled Push | C\n    - 20 m / P: 0 s\n    - 20 m / P: 0 s\n    - 20 m / P: 0 s\n- Wall Ball Shot | C\n    - 15 reps @ 9 kg / P: 0 s\n    - 15 reps @ 9 kg / P: 0 s\n    - 15 reps @ 9 kg / P: 0 s\n- Kettlebell Swing (Russian) | C\n    - 20 reps @ 24 kg / P: 90 s\n    - 20 reps @ 24 kg / P: 90 s\n    - 20 reps @ 24 kg / P: 90 s\n\nCool-Down | 7 min | Flexibilität & Erholung\n- Couch-Stretch links | A\n    - 45 s\n- Couch-Stretch rechts | A\n    - 45 s\n- Butterfly Stretch | –\n    - 60 s\n- Downward Dog to Cobra | –\n    - 60 s\n- Happy Baby Pose | –\n    - 60 s\n- Thorakale Extension über die Schaumstoffrolle | –\n    - 90 s', 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 