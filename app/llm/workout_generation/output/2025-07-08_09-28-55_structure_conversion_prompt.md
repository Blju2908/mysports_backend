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
Workout: Push Day - Kraft & Muskelaufbau (≈60 min | Fokus: Brust, Schultern, Trizeps, Core)

Warm-Up | 10 min | Mobilisation und Gelenkvorbereitung
- Jumping Jacks | –
    - 60 s / P: 0 s
- Arm Circles | –
    - 15 reps / P: 0 s
- Torso Twists | –
    - 16 reps / P: 0 s
- World's Greatest Hip Opener links | –
    - 6 reps / P: 0 s
- World's Greatest Hip Opener rechts | –
    - 6 reps / P: 0 s
- Cat-Cow Flow | –
    - 10 reps / P: 0 s

Main | 45 min | Klassisches Kraft- und Muskelaufbau-Training für den Oberkörper mit Core-Fokus
- Barbell Bench Press | –
    - 8 @ 85 kg / P: 120 s
    - 6 @ 87.5 kg / P: 120 s
    - 8 @ 82.5 kg / P: 120 s
    - 8 @ 82.5 kg / P: 120 s
- Strict Barbell Overhead Press | –
    - 10 @ 35 kg / P: 90 s
    - 8 @ 37.5 kg / P: 90 s
    - 8 @ 37.5 kg / P: 90 s
- Dumbbell Incline Bench Press | –
    - 10 @ 22.5 kg / P: 90 s
    - 9 @ 22.5 kg / P: 90 s
    - 8 @ 22.5 kg / P: 90 s
- Lateral Raise with Dumbbells | –
    - 12 @ 10 kg / P: 60 s
    - 12 @ 10 kg / P: 60 s
    - 10 @ 12.5 kg / P: 60 s
- Cable Triceps Push-down with Rope | –
    - 12 @ 20 kg / P: 60 s
    - 12 @ 22.5 kg / P: 60 s
    - 10 @ 22.5 kg / P: 60 s
- Plank Hold | –
    - 45 s / P: 60 s
    - 45 s / P: 60 s
    - 45 s / P: 60 s
- Leg Raise | –
    - 12 reps / P: 60 s
    - 12 reps / P: 60 s
    - 12 reps / P: 60 s

Cool-Down | 5 min | Dehnung der beanspruchten Muskelgruppen
- Doorway Pec Stretch | –
    - 45 s
- Cross-Body Shoulder Stretch links | –
    - 45 s
- Cross-Body Shoulder Stretch rechts | –
    - 45 s
- Triceps Overhead Stretch links | –
    - 45 s
- Triceps Overhead Stretch rechts | –
    - 45 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 