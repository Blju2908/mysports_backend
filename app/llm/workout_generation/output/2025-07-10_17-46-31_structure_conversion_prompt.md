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
Workout: Lower Body Focus (≈60 min | Fokus: Beine, Gesäß, Core | Description: Kraftsteigerung und Muskelentwicklung. Gezielt auf niedrige Belastung der Knie und Mobilität der Hüfte. Ausgewogen mit gesunden Intensitäts- und Volumensteuerungen.)

Warm-Up | 10 Minuten | Aufwärmung der Gelenke und Mobilisierung
- Jumping Jacks | –
    - 60 s / P: 30 s
- Hip Circles | –
    - 10 reps
- World's Greatest Stretch [unilateral] | A
    - 6 reps
- World's Greatest Stretch [unilateral] | A
    - 6 reps
- 90/90 Hip Switch | –
    - 60 s

Main | 40 Minuten | Schwerpunkt auf Bein- und Rumpfkraftaufbau
- Barbell Box Squat | –
    - 10 @ 60 kg / P: 2 min
    - 8 @ 70 kg / P: 2 min
    - 6 @ 75 kg / P: 2 min
- Bulgarian Split Squat with Dumbbells [unilateral] | B
    - 10 @ 20 kg / P: 90 s
    - 8 @ 22.5 kg / P: 90 s
- Bulgarian Split Squat with Dumbbells [unilateral] | B
    - 10 @ 20 kg / P: 90 s
    - 8 @ 22.5 kg / P: 90 s
- Dumbbell Romanian Deadlift | –
    - 12 @ 25 kg / P: 2 min
    - 10 @ 27.5 kg / P: 2 min
    - 8 @ 30 kg / P: 2 min
- Glute Bridge | –
    - 15 reps / P: 90 s
    - 15 reps / P: 90 s
    - 15 reps / P: 90 s

Cool-Down | 10 Minuten | Entspannung und Dehnung für Muskelerholung
- Hamstring Stretch (Standing) [unilateral] | C
    - 45 s
- Hamstring Stretch (Standing) [unilateral] | C
    - 45 s
- Hip Flexor Stretch (Kneeling) [unilateral] | D
    - 60 s
- Hip Flexor Stretch (Kneeling) [unilateral] | D
    - 60 s
- Child's Pose | –
    - 60 s

```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 