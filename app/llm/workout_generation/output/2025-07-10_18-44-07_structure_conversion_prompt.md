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
Workout: Lower Body & Core Focus (≈60 min | Fokus: Beine, Core | Description: Schwerpunkt auf Bein- und Core-Training, frische Beine. Progressive Belastungssteuerung. Kein Überlastungsrisiko für Knie. Keine Supersets.)

Warm-Up | 10 min | Ganzkörper-Aktivierung, Schwerpunkt Hüfte
- Jumping Jacks | –
    - 60 s
- Hip Circles | –
    - 10 reps
- 90/90 Hip Switch | –
    - 60 s
- World's Greatest Stretch [unilateral] | A
    - 6 reps links
    - 6 reps rechts

Main | 40 min | Beine und Core im Fokus, moderate Intensität
- Bulgarian Split Squat with Dumbbells | –
    - 12 @ 20 kg / P: 90 s
    - 10 @ 22,5 kg / P: 90 s
    - 8 @ 25 kg / P: 90 s
- Dumbbell Romanian Deadlift | –
    - 10 @ 30 kg / P: 90 s
    - 10 @ 32,5 kg / P: 90 s
    - 8 @ 35 kg / P: 90 s
- Glute Bridge | –
    - 12 reps / P: 60 s
    - 12 reps / P: 60 s
    - 10 reps / P: 60 s
- Single-Leg Calf Raise [unilateral] | B
    - 15 reps links / P: 60 s
    - 15 reps rechts / P: 60 s
- Russian Twist | –
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s
    - 12 reps / P: 60 s
- Hollow Body Hold | –
    - 30 s / P: 30 s
    - 30 s / P: 30 s
    - 30 s / P: 30 s

Cool-Down | 10 min | Dehnung für Regeneration und Mobilität
- Child's Pose | –
    - 60 s
- Hamstring Stretch (Standing) [unilateral] | C
    - 45 s links
    - 45 s rechts
- Hip Flexor Stretch (Kneeling) [unilateral] | D
    - 60 s links
    - 60 s rechts
- Cat-Cow Flow | –
    - 60 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 