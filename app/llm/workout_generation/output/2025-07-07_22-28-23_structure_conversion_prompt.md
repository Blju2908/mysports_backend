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
Workout: Pull Day - Rücken & Bizeps Kraft (≈60 min | Fokus: Rücken, Bizeps, Core, Muskelaufbau)

Warm-Up | 10 min | Mobilisierung und Aktivierung des Oberkörpers und der Hüfte
- Jumping Jacks | –
    - 60 s
- Arm Circles | –
    - 15 reps
    - 15 reps
- Thoracic Spine Rotation (Quadruped) links | –
    - 8 reps
- Thoracic Spine Rotation (Quadruped) rechts | –
    - 8 reps
- World's Greatest Hip Opener links | –
    - 30 s
- World's Greatest Hip Opener rechts | –
    - 30 s
- Cat-Cow Flow | –
    - 10 reps

Main | 45 min | Kraft- und Muskelaufbau für Rücken, Bizeps und Core
- Pull-up | –
    - 8 reps / P: 90 s
    - 7 reps / P: 90 s
    - 6 reps / P: 90 s
    - 6 reps / P: 90 s
- Barbell Row | –
    - 10 @ 60 kg / P: 90 s
    - 8 @ 65 kg / P: 90 s
    - 8 @ 65 kg / P: 90 s
    - 6 @ 70 kg / P: 90 s
- Lat Pulldown | –
    - 10 @ 65 kg / P: 75 s
    - 10 @ 65 kg / P: 75 s
    - 8 @ 70 kg / P: 75 s
- Face Pull | –
    - 15 @ 20 kg / P: 60 s
    - 15 @ 20 kg / P: 60 s
    - 12 @ 22.5 kg / P: 60 s
- Cable Biceps Curl with Straight Bar | –
    - 12 @ 15 kg / P: 60 s
    - 10 @ 17.5 kg / P: 60 s
    - 10 @ 17.5 kg / P: 60 s
- Dragon Flag on Flat Bench | –
    - 8 reps / P: 60 s
    - 6 reps / P: 60 s
    - 6 reps / P: 60 s

Cool-Down | 5 min | Dehnung und Entspannung
- Child's Pose | –
    - 60 s
- Cat Stretch | –
    - 60 s
- Supine Twist links | –
    - 45 s
- Supine Twist rechts | –
    - 45 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 