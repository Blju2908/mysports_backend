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
Workout: Kraft & Ästhetik: Push Power (≈60 min | Fokus: Brust, Schultern, Trizeps, Kraft, Muskelaufbau)

Warm-Up | 7 min | Vorbereitung auf das Oberkörpertraining
- Arm Circles | –
    - 15 reps
    - 15 reps
- Shoulder Pass-Through with Resistance Band | –
    - 12 reps
    - 12 reps
- Cat-Cow Flow | –
    - 10 reps
    - 10 reps

Main | 48 min | Klassisches Kraft- und Muskelaufbau-Training für den Oberkörper
- Barbell Bench Press | –
    - 5 @ 75 kg / P: 180 s
    - 5 @ 75 kg / P: 180 s
    - 8 @ 65 kg / P: 120 s
    - 8 @ 65 kg / P: 120 s
- Strict Barbell Overhead Press | –
    - 6 @ 40 kg / P: 150 s
    - 6 @ 45 kg / P: 150 s
    - 8 @ 35 kg / P: 120 s
- Dumbbell Incline Bench Press | –
    - 8 @ 22.5 kg / P: 90 s
    - 8 @ 22.5 kg / P: 90 s
    - 10 @ 20 kg / P: 90 s
- Lateral Raise with Dumbbells | –
    - 12 @ 10 kg / P: 60 s
    - 12 @ 10 kg / P: 60 s
    - 15 @ 7.5 kg / P: 60 s
- Cable Triceps Push-down with Straight Bar | –
    - 10 @ 30 kg / P: 60 s
    - 10 @ 30 kg / P: 60 s
    - 12 @ 25 kg / P: 60 s
- Seated Dumbbell Overhead Triceps Extension | –
    - 10 @ 15 kg / P: 60 s
    - 10 @ 15 kg / P: 60 s
    - 12 @ 12.5 kg / P: 60 s

Cool-Down | 5 min | Dehnung und Regeneration
- Doorway Pec Stretch | –
    - 60 s
- Cross-Body Shoulder Stretch rechts | –
    - 30 s
- Cross-Body Shoulder Stretch links | –
    - 30 s
- Triceps Overhead Stretch rechts | –
    - 30 s
- Triceps Overhead Stretch links | –
    - 30 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 