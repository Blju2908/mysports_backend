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
[{'type': 'text', 'text': 'Workout: Hyrox Hybrid Kraft & Ausdauer (≈60 min | Fokus: Kraft, Ausdauer, funktionale Fitness)\n\nWarm-Up | 10 min | Mobilisierung & Herzfrequenzsteigerung\n- Armkreisen | –\n    - 10 reps / P: 15 s\n    - 10 reps / P: 15 s\n- Dynamische Ausfallschritte | –\n    - 8 reps / P: 15 s\n    - 8 reps / P: 15 s\n- Air Squat | –\n    - 10 reps / P: 15 s\n    - 10 reps / P: 15 s\n- Jumping Jacks | –\n    - 60 s / P: 30 s\n    - 60 s / P: 30 s\n\nMain | 45 min | Kraftblock & funktionaler Hyrox-Zirkel\n- Kniebeuge mit Langhantel | –\n    - 8 @ 80 kg / P: 120 s\n    - 8 @ 80 kg / P: 120 s\n    - 8 @ 80 kg / P: 120 s\n- Bankdrücken mit Langhantel | –\n    - 8 @ 60 kg / P: 120 s\n    - 8 @ 60 kg / P: 120 s\n    - 8 @ 60 kg / P: 120 s\n- Sumo-Kreuzheben mit Langhantel | –\n    - 6 @ 120 kg / P: 120 s\n    - 6 @ 120 kg / P: 120 s\n    - 6 @ 120 kg / P: 120 s\n- Ski Ergometer | C\n    - 300 m / P: 60 s\n    - 300 m / P: 60 s\n    - 300 m / P: 60 s\n- Sled Push | C\n    - 20 m / P: 60 s\n    - 20 m / P: 60 s\n    - 20 m / P: 60 s\n- Wall Ball Shot | C\n    - 15 reps / P: 60 s\n    - 15 reps / P: 60 s\n    - 15 reps / P: 60 s\n- Farmers Walk mit Kurzhanteln | C\n    - 40 m / P: 60 s\n    - 40 m / P: 60 s\n    - 40 m / P: 60 s\n\nCool-Down | 5 min | Beweglichkeit & Erholung\n- Kniender Hüftbeuger-Stretch | –\n    - 30 s\n- Waden-Dehnung an der Wand | –\n    - 30 s\n- Butterfly Stretch | –\n    - 30 s\n- Couch-Stretch | –\n    - 30 s\n- Kindhaltung | –\n    - 60 s', 'annotations': []}]

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 