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
Workout: Upper Body Strength (≈60 min | Fokus: Oberkörperkraft, Muskelaufbau | Description: Fokus auf Push- und Pull-Übungen mit Betonung auf Progression. Priorisierung von Brust-, Schulter- und Rückenmuskelgruppen. Anpassung der Intensitäten basierend auf dem Erholungsstatus. Begrenzte Super-Sets, um den klassischen Krafttraining-Stil zu respektieren.)

Warm-Up | 10 Minuten | Leichte Mobilisierung und Herz-Kreislauf-Anregung
- Jumping Jacks | –
    - 60 s
- Arm Circles | –
    - 15 reps
- World's Greatest Stretch | –
    - 6 reps
- 90/90 Hip Switch | –
    - 60 s

Main | 45 Minuten | Oberkörper-Push und -Pull im Fokus, ohne Überlastung
- Barbell Bench Press | –
    - 8 @ 80 kg / P: 120 s
    - 6 @ 85 kg / P: 120 s
    - 5 @ 90 kg / P: 180 s
- Dumbbell Row | –
    - 10 @ 30 kg / P: 90 s
    - 10 @ 32.5 kg / P: 90 s
    - 8 @ 35 kg / P: 120 s
- Dumbbell Shoulder Press | –
    - 12 @ 20 kg / P: 90 s
    - 10 @ 22.5 kg / P: 90 s
    - 8 @ 25 kg / P: 120 s
- Face Pull | –
    - 15 @ 20 kg / P: 60 s
    - 15 @ 25 kg / P: 60 s
    - 12 @ 25 kg / P: 90 s
- EZ Bar Skullcrusher | –
    - 12 @ 25 kg / P: 60 s
    - 10 @ 30 kg / P: 60 s
    - 8 @ 35 kg / P: 90 s

Cool-Down | 5 Minuten | Entspannung und Mobilisierung
- Child's Pose | –
    - 60 s
- Cross-Body Shoulder Stretch links | –
    - 45 s
- Cross-Body Shoulder Stretch rechts | –
    - 45 s
- Triceps Overhead Stretch links | –
    - 45 s
- Triceps Overhead Stretch rechts | –
    - 45 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 