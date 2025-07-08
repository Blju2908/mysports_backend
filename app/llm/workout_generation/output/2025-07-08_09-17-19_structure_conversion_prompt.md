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
Workout: Rücken & Bizeps Kraft mit Core Fokus (≈60 min | Fokus: Rücken, Bizeps, Core, Kraft)

Warm-Up | 10 min | Dynamische Mobilisierung für Schultern, Wirbelsäule und Hüfte
- Jumping Jacks | –
    - 60 s / P: 0 s
- Arm Circles | –
    - 15 reps / P: 0 s
    - 15 reps / P: 0 s
- Thoracic Spine Rotation links | –
    - 8 reps / P: 0 s
- Thoracic Spine Rotation rechts | –
    - 8 reps / P: 0 s
- 90/90 Hip Switch | –
    - 60 s / P: 0 s
- World's Greatest Stretch links | –
    - 6 reps / P: 0 s
- World's Greatest Stretch rechts | –
    - 6 reps / P: 0 s

Main | 45 min | Klassisches Krafttraining für Rücken und Bizeps mit intensivem Core-Block
- Pull-up | –
    - 8 reps / P: 90 s
    - 7 reps / P: 90 s
    - 6 reps / P: 90 s
- Barbell Row | –
    - 8 @ 65 kg / P: 90 s
    - 10 @ 60 kg / P: 90 s
    - 10 @ 60 kg / P: 90 s
- Lat Pulldown | –
    - 10 @ 70 kg / P: 75 s
    - 12 @ 65 kg / P: 75 s
    - 12 @ 65 kg / P: 75 s
- Face Pull | –
    - 15 @ 20 kg / P: 60 s
    - 15 @ 20 kg / P: 60 s
    - 15 @ 20 kg / P: 60 s
- EZ-Bar Curl | –
    - 10 @ 30 kg / P: 60 s
    - 12 @ 27.5 kg / P: 60 s
    - 12 @ 27.5 kg / P: 60 s
- Side Plank links | A
    - 30 s / P: 0 s
- Side Plank rechts | A
    - 30 s / P: 60 s
- Reverse Crunch | A
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s

Cool-Down | 5 min | Dehnung und Entspannung
- Cat-Cow Flow | –
    - 60 s / P: 0 s
- Child's Pose | –
    - 60 s / P: 0 s
- Lying Glute Stretch links | –
    - 45 s / P: 0 s
- Lying Glute Stretch rechts | –
    - 45 s / P: 0 s
- Supine Twist links | –
    - 45 s / P: 0 s
- Supine Twist rechts | –
    - 45 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 