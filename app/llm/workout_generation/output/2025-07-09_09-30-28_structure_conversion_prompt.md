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
Workout: Kraft & Muskelaufbau: Oberkörper Druck (≈60 min | Fokus: Brust, Schultern, Trizeps)

Warm-Up | 10 min | Dynamische Mobilisierung für Oberkörper und Schultern
- Arm Circles | –
    - 15 reps / P: 0 s
    - 15 reps / P: 30 s
- Shoulder Pass-Through with Resistance Band | –
    - 12 reps / P: 0 s
    - 12 reps / P: 30 s
- Push-up | –
    - 10 reps / P: 0 s
    - 10 reps / P: 30 s
- Cat-Cow Flow | –
    - 10 reps / P: 0 s
    - 10 reps / P: 30 s

Main | 45 min | Klassisches Kraft- und Muskelaufbautraining für Druckmuskulatur
- Barbell Bench Press | –
    - 8 @ 50 kg / P: 60 s
    - 5 @ 65 kg / P: 90 s
    - 6 @ 77.5 kg / P: 120 s
    - 6 @ 77.5 kg / P: 120 s
    - 6 @ 77.5 kg / P: 120 s
- Strict Barbell Overhead Press | –
    - 8 @ 30 kg / P: 60 s
    - 6 @ 47.5 kg / P: 120 s
    - 6 @ 47.5 kg / P: 120 s
    - 6 @ 47.5 kg / P: 120 s
- Dumbbell Incline Bench Press | –
    - 10 @ 30 kg / P: 90 s
    - 10 @ 30 kg / P: 90 s
    - 10 @ 30 kg / P: 90 s
- Lateral Raise with Dumbbells | –
    - 12 @ 12.5 kg / P: 60 s
    - 12 @ 12.5 kg / P: 60 s
    - 12 @ 12.5 kg / P: 60 s
- Cable Fly | A
    - 12 @ 22.5 kg / P: 0 s
    - 12 @ 22.5 kg / P: 0 s
    - 12 @ 22.5 kg / P: 0 s
- Cable Triceps Push-down with Straight Bar | A
    - 12 @ 37.5 kg / P: 90 s
    - 12 @ 37.5 kg / P: 90 s
    - 12 @ 37.5 kg / P: 90 s

Cool-Down | 5 min | Dehnung und Entspannung
- Doorway Pec Stretch | –
    - 30 s / P: 30 s
- Triceps Overhead Stretch links | A
    - 30 s / P: 0 s
- Triceps Overhead Stretch rechts | A
    - 30 s / P: 60 s
- Cross-Body Shoulder Stretch links | B
    - 30 s / P: 0 s
- Cross-Body Shoulder Stretch rechts | B
    - 30 s / P: 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 