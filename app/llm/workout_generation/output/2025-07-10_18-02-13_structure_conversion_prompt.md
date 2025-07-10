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
Workout: Leg Day - Beine & Glutes (≈60 min | Fokus: Beine, Glutes | Description: Fokus auf Bein- und Gesäßmuskelaufbau nach Meniskus-OP, schonende Knie-Optionen.)

Warm-Up | 10 Minuten | Dynamische Beweglichkeit für Knie und Hüfte
- 90/90 Hip Switch | –
    - 10 reps / P: 30 s
- World's Greatest Stretch rechts | –
    - 5 reps / P: 30 s
- World's Greatest Stretch links | –
    - 5 reps / P: 30 s
- Jumping Jacks | –
    - 60 s

Main | 45 Minuten | Kraftsteigerung und Muskelentwicklung für Unterkörper
- Barbell Box Squat | –
    - 8 @ 60 kg / P: 120 s
    - 8 @ 70 kg / P: 120 s
    - 6 @ 75 kg / P: 120 s
- Bulgarian Split Squat with Dumbbells | Superset A
    - 10 @ 12 kg / P: 60 s
    - 10 @ 14 kg / P: 60 s
- Bulgarian Split Squat with Dumbbells | Superset A
    - 10 @ 12 kg / P: 60 s
    - 10 @ 14 kg / P: 60 s
- Barbell Romanian Deadlift | –
    - 10 @ 55 kg / P: 90 s
    - 10 @ 60 kg / P: 90 s
    - 8 @ 65 kg / P: 90 s
- Calf Raise on Machine | –
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s
    - 12 reps / P: 60 s

Cool-Down | 5 Minuten | Regeneration und Entspannung der beanspruchten Muskulatur
- Child's Pose | –
    - 60 s
- Hamstring Stretch rechts (Stehend) | –
    - 45 s
- Hamstring Stretch links (Stehend) | –
    - 45 s
- Butterfly Stretch | –
    - 60 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 