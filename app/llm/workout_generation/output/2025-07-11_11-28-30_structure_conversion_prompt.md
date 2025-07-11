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
```
Workout: Push-Fokus Kraft & Muskelaufbau (≈60 min | Fokus: Brust, Schultern, Trizeps | Description: Fokussiert auf Push-Muskulatur. Unterstützung bei der Muscle-Up-Zielsetzung. Ermöglicht funktionelle Kraftsteigerung.)

Warm-Up | 10 Minuten | Mobilisation und Aktivierung der Oberkörpermuskulatur
- Arm Circles | –
    - 15 reps
    - 15 reps
- Shoulder Pass-Through with Resistance Band | –
    - 12 reps
    - 12 reps
- Band Pull-Aparts | –
    - 15 reps
    - 15 reps

Main | 45 Minuten | Schweres Push-Training mit Progressionsfokus
- Barbell Bench Press | –
    - 10 @ 60 kg / P: 180 s
    - 8 @ 70 kg / P: 180 s
    - 6 @ 80 kg / P: 180 s
- Dumbbell Shoulder Press | –
    - 12 @ 22.5 kg / P: 120 s
    - 10 @ 25 kg / P: 120 s
    - 8 @ 27.5 kg / P: 120 s
- Dumbbell Fly | –
    - 12 @ 15 kg / P: 90 s
    - 12 @ 17.5 kg / P: 90 s
    - 12 @ 20 kg / P: 90 s
- Close-Grip Barbell Bench Press | –
    - 10 @ 50 kg / P: 120 s
    - 8 @ 55 kg / P: 120 s
    - 6 @ 60 kg / P: 120 s

Cool-Down | 5 Minuten | Lockerung und Entspannung der Push-Muskulatur
- Doorway Pec Stretch | –
    - 30 s
- Triceps Overhead Stretch links | –
    - 30 s
- Triceps Overhead Stretch rechts | –
    - 30 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 