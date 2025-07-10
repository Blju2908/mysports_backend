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
Workout: Leg & Lower-Body Focus (≈60 min | Fokus: Beine, Glutes, Core | Description: Aufbauend auf vorangegangene Push- und Pull-Trainings. Fokus auf Beinmuskulatur mit Rücksicht auf Kniebelastung. Integration von Core-Übungen zur Stabilität.)

Warm-Up | 10 Minuten | Mobilisierung und Aktivierung des Unterkörpers
- 90/90 Hip Switch | –
    - 12 reps
- Air Squat | –
    - 15 reps
- Hip Circles | –
    - 10 reps
- World's Greatest Hip Opener rechts | –
    - 6 reps
- World's Greatest Hip Opener links | –
    - 6 reps

Main | 40 Minuten | Intensives Bein- und Core-Training
- Barbell Deadlift | –
    - 8 @ 70 kg / P: 120 s
    - 8 @ 80 kg / P: 120 s
    - 6 @ 90 kg / P: 120 s
- Bulgarian Split Squat with Dumbbells rechts | B
    - 10 @ 12 kg / P: 60 s
    - 10 @ 12 kg / P: 60 s
- Bulgarian Split Squat with Dumbbells links | B
    - 10 @ 12 kg / P: 120 s
    - 10 @ 12 kg / P: 120 s
- Glute Bridge | –
    - 15 reps / P: 90 s
    - 15 reps / P: 90 s
    - 12 reps / P: 90 s
- Single-Leg Glute Bridge rechts | C
    - 12 reps / P: 60 s
    - 12 reps / P: 60 s
- Single-Leg Glute Bridge links | C
    - 12 reps / P: 120 s
    - 12 reps / P: 120 s
- Plank Hold | –
    - 60 s / P: 60 s
    - 45 s / P: 60 s
    - 45 s / P: 60 s

Cool-Down | 10 Minuten | Dehnung und Entspannung des Unterkörpers
- Child's Pose | –
    - 60 s
- Kneeling Quad Stretch rechts | –
    - 45 s
- Kneeling Quad Stretch links | –
    - 45 s
- Standing Calf Stretch Against Wall rechts | –
    - 45 s
- Standing Calf Stretch Against Wall links | –
    - 45 s
- Supine Twist rechts | –
    - 45 s
- Supine Twist links | –
    - 45 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 