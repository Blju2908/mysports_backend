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
Workout: Total Body & Core Focus (≈60 min | Fokus: Kraft, Core, Push/Pull Balance | Description: Zielt auf funktionelle Kraft und Core. Vermeidet Überlastung des Brust/Schulterbereichs nach Push-Session. Rückgrat durch vorrangiges Core-Element. Unterstützt Marathon-Ziel mit Stabilität und Ausdauer. Stärkerer Pull-Bias für besseres Bewegungsmuster.)

Warm-Up | 10 Minuten | Ganzkörper-Mobilisierung und Fokus auf Stabilität
- Arm Circles | –
    - 15 reps / P: 30 s
    - 15 reps / P: 30 s
- Inchworm Walkout | –
    - 5 reps / P: 30 s
    - 5 reps / P: 30 s
- Spider Lunge with Rotation links | A
    - 10 reps / P: 15 s
- Spider Lunge with Rotation rechts | A
    - 10 reps / P: 15 s

Main | 40 Minuten | Core und Pull Fokussierung mit ergänzenden Push-Elementen
- Barbell Deadlift | –
    - 6 @ 90 kg / P: 120 s
    - 6 @ 90 kg / P: 120 s
    - 6 @ 90 kg / P: 120 s
- Dumbbell Bench Press | –
    - 10 @ 25 kg / P: 90 s
    - 10 @ 25 kg / P: 90 s
    - 10 @ 25 kg / P: 90 s
- Pull-up | –
    - 8 reps / P: 90 s
    - 8 reps / P: 90 s
    - 8 reps / P: 90 s
- Single-Arm Dumbbell Row links | B
    - 10 @ 30 kg / P: 15 s
- Single-Arm Dumbbell Row rechts | B
    - 10 @ 30 kg / P: 60 s
- Plank Hold | –
    - 60 s / P: 60 s
    - 60 s / P: 60 s
    - 60 s / P: 60 s

Cool-Down | 10 Minuten | Entspannung und Flexibilität fördern
- Doorway Pec Stretch | –
    - 30 s / P: 15 s
- Child's Pose | –
    - 60 s / P: 15 s
- Triceps Overhead Stretch links | C
    - 30 s / P: 15 s
- Triceps Overhead Stretch rechts | C
    - 30 s / P: 15 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 