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
Workout: Pull Day - Rücken, Bizeps & Core (≈60 min | Fokus: Kraft, Muskelaufbau, Core)

Warm-Up | 10 min | Dynamische Bewegung und Mobilisation
- Jumping Jacks | –
    - 60 s
- Arm Circles | –
    - 15 reps
    - 15 reps
- Cat-Cow Flow | –
    - 10 reps
- World's Greatest Stretch | –
    - 6 reps
    - 6 reps
- 90/90 Hip Switch | –
    - 60 s

Main | 45 min | Aufbau von Rücken- und Bizepskraft, Stärkung des Cores
- Pull-up | –
    - 8 reps / P: 90 s
    - 7 reps / P: 90 s
    - 6 reps / P: 90 s
    - 6 reps / P: 90 s
- Barbell Row | –
    - 8 @ 65 kg / P: 90 s
    - 8 @ 70 kg / P: 90 s
    - 6 @ 75 kg / P: 90 s
    - 6 @ 75 kg / P: 90 s
- Lat Pulldown | –
    - 10 @ 65 kg / P: 75 s
    - 10 @ 70 kg / P: 75 s
    - 8 @ 75 kg / P: 75 s
- Face Pull | –
    - 15 @ 20 kg / P: 60 s
    - 15 @ 22.5 kg / P: 60 s
    - 12 @ 25 kg / P: 60 s
- Barbell Curl | –
    - 10 @ 25 kg / P: 60 s
    - 10 @ 27.5 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
- Hanging Leg Raise | –
    - 12 reps / P: 45 s
    - 12 reps / P: 45 s
    - 10 reps / P: 45 s

Cool-Down | 5 min | Dehnung und Entspannung
- Child's Pose | –
    - 60 s
- Doorway Pec Stretch | –
    - 45 s
    - 45 s
- Cross-Body Shoulder Stretch links | –
    - 45 s
- Cross-Body Shoulder Stretch rechts | –
    - 45 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 