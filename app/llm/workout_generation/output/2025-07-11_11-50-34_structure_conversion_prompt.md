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
Workout: Upper Body Strength and Mobility Session (≈60 min | Fokus: Kraftaufbau, Mobilität, Funktionelle Stärke | Description: Fokussierte auf Oberkörperkraft. Stretching zwischen den Übungen integriert. Balance von Push/Pull-Übungen.)

Warm-Up | 10 Minuten | Lockerung und leichte Aktivierung 
- Arm Circles | –
    - 15 reps
    - 15 reps
- Inchworm Walkout | –
    - 5 reps
    - 5 reps
- Push-up | –
    - 10 reps
    - 10 reps

Main | 45 Minuten | Starke Betonung auf Push-Übungen und funktionelle Elemente
- Barbell Bench Press | –
    - 6 @ 80 kg / P: 120 s
    - 6 @ 82.5 kg / P: 120 s
    - 6 @ 85 kg / P: 120 s
    - 6 @ 85 kg / P: 120 s
- Dumbbell Shoulder Press | –
    - 8 @ 22 kg / P: 90 s
    - 8 @ 22 kg / P: 90 s
    - 8 @ 22 kg / P: 90 s
- Cable Fly | A
    - 12 @ 25 kg / P: 60 s
    - 12 @ 25 kg / P: 60 s
    - 12 @ 25 kg / P: 60 s
- Lat Pulldown | –
    - 10 @ 65 kg / P: 90 s
    - 10 @ 65 kg / P: 90 s
    - 10 @ 65 kg / P: 90 s
- Dumbbell Hammer Curl | B
    - 12 @ 12 kg / P: 60 s
    - 12 @ 12 kg / P: 60 s
    - 12 @ 12 kg / P: 60 s
- Triceps Overhead Stretch links | B
    - 30 s
- Triceps Overhead Stretch rechts | B
    - 30 s

Cool-Down | 5 Minuten | Sanfte Dehnung und Entspannung
- Child's Pose | –
    - 60 s
- Doorway Pec Stretch | –
    - 30 s
- Kneeling Quad Stretch links | –
    - 30 s
- Kneeling Quad Stretch rechts | –
    - 30 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 