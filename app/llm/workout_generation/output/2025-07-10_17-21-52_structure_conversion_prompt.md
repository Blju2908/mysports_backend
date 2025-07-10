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
Workout: Lower Body Focus (≈60 min | Fokus: Beine, Glutes, Core | Description: Fokus auf Beinmuskulatur mit moderater Intensität, Regeneration der Oberkörpermuskeln. Unterstützt Muskelwachstum und verbessert die Körperästhetik.)

Warm-Up | 10 | Prepare the lower body, enhance mobility, and increase heart rate.
- Jumping Jacks | –
    - 60 s
- Air Squat | –
    - 15 reps
- World's Greatest Stretch links | –
    - 30 s
- World's Greatest Stretch rechts | –
    - 30 s
- Hip Circles | –
    - 10 reps

Main | 40 | Focused on legs, implements compound movements and moderate intensity.
- Barbell Deadlift | –
    - 8 @ 100 kg / P: 180 s
    - 8 @ 100 kg / P: 180 s
    - 6 @ 110 kg / P: 180 s
- Barbell Box Squat | –
    - 10 @ 60 kg / P: 120 s
    - 10 @ 60 kg / P: 120 s
    - 8 @ 70 kg / P: 120 s
- Bulgarian Split Squat with Dumbbells links | B
    - 10 @ 20 kg / P: 60 s
    - 10 @ 22.5 kg / P: 60 s
- Bulgarian Split Squat with Dumbbells rechts | B
    - 10 @ 20 kg / P: 60 s
    - 10 @ 22.5 kg / P: 120 s
- Single-Leg Calf Raise links | –
    - 12 reps
    - 12 reps
- Single-Leg Calf Raise rechts | –
    - 12 reps
    - 12 reps

Cool-Down | 10 | Facilitate recovery and improve flexibility.
- 90/90 Hip Switch | –
    - 60 s
- Hamstring Stretch (Standing) links | –
    - 45 s
- Hamstring Stretch (Standing) rechts | –
    - 45 s
- Child's Pose | –
    - 60 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 