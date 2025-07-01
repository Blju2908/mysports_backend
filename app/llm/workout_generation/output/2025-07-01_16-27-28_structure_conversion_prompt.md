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
      "position": 0,
      "exercises": [
        {
          "name": "Jumping Jacks",
          "position": 0,
          "sets": [
            {"values": [null, null, 60, null, null], "position": 0}
          ]
        },
        {
          "name": "Armkreisen",
          "position": 1,
          "sets": [
            {"values": [null, 10, null, null, null], "position": 0}
          ]
        }
      ]
    },
    {
      "name": "Hauptteil",
      "description": "Krafttraining Superset",
      "position": 1,
      "exercises": [
        {
          "name": "Kurzhantel Bankdrücken",
          "superset_id": "A",
          "position": 0,
          "sets": [
            {"values": [20, 12, null, null, 60], "position": 0},
            {"values": [20, 10, null, null, 60], "position": 1},
            {"values": [20, 8, null, null, 60], "position": 2}
          ]
        },
        {
          "name": "Kurzhantel Rudern",
          "superset_id": "A",
          "position": 1,
          "sets": [
            {"values": [20, 12, null, null, 0], "position": 0},
            {"values": [20, 10, null, null, 0], "position": 1},
            {"values": [20, 8, null, null, 0], "position": 2}
          ]
        }
      ]
    },
    {
      "name": "Cooldown",
      "description": "Dehnung und Entspannung",
      "position": 2,
      "exercises": [
        {
          "name": "Brustdehnung",
          "position": 0,
          "sets": [
            {"values": [null, null, 30, null, null], "position": 0}
          ]
        }
      ]
    }
  ]
}
```

# Input
Workout: Hyrox-Style Kraft & Ausdauer II (≈60 min | Fokus: Kraft, Ausdauer, Funktionalität, Ästhetik)

Warm-Up | 8 min | Bereit für maximale Leistung
- High Knees | –
    - 60 s / P: 15 s
- Butt Kicks | –
    - 60 s / P: 15 s
- Dynamic Walking Lunges | –
    - 10 reps / P: 15 s
- World's Greatest Stretch | –
    - 8 reps / P: 15 s

Main | 47 min | Kraftaufbau & Hyrox-Zirkel
- Conventional Deadlift | –
    - 5 @ 100 kg / P: 120 s
    - 5 @ 115 kg / P: 120 s
    - 4 @ 120 kg / P: 120 s
    - 3 @ 125 kg / P: 120 s
- Incline Bench Press | –
    - 8 @ 50 kg / P: 90 s
    - 8 @ 60 kg / P: 90 s
    - 6 @ 65 kg / P: 90 s
- Barbell Row | –
    - 10 @ 50 kg / P: 90 s
    - 8 @ 60 kg / P: 90 s
    - 8 @ 65 kg / P: 90 s
- Ski Ergometer | A
    - 300 m / P: 30 s
- Sled Pull | B
    - 20 m @ 60 kg / P: 30 s
- Burpee | C
    - 12 reps / P: 90 s
- Ski Ergometer | A
    - 300 m / P: 30 s
- Sled Pull | B
    - 20 m @ 60 kg / P: 30 s
- Burpee | C
    - 12 reps / P: 90 s
- Ski Ergometer | A
    - 300 m / P: 30 s
- Sled Pull | B
    - 20 m @ 60 kg / P: 30 s
- Burpee | C
    - 12 reps / P: 90 s
- Hollow Body Hold | –
    - 45 s / P: 60 s
    - 45 s / P: 60 s
- Leg Raise | –
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s

Cool-Down | 5 min | Flexibilität & Erholung
- Hamstring Stretch (Seated Forward Fold) | –
    - 60 s
- Couch Stretch | –
    - 30 s
- Couch Stretch | –
    - 30 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 