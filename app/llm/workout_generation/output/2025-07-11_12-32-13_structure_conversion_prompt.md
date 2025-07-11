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
Workout: Leg Strength & Endurance Builder (≈60 min | Fokus: Beine, Funktionale Kraft, Ausdauer | Description: Fokus auf maximale Bein- und Glutealkraft nach optimaler Regeneration; Integration von Grundübungen und unilateralen Bewegungen; Stärkung des Rumpfes für funktionelle Leistung; Ermöglicht individuelle Dehnungen in den Satzpausen.)

Warm-Up | 10 min | Vorbereitung der Muskulatur und Gelenke auf die Belastung, Steigerung der Herzfrequenz.
- Jumping Jacks | –
    - 60 s / P: 0 s
- Leg Swings Front-to-Back links | –
    - 10 reps / P: 0 s
- Leg Swings Front-to-Back rechts | –
    - 10 reps / P: 0 s
- Leg Swings Side-to-Side links | –
    - 10 reps / P: 0 s
- Leg Swings Side-to-Side rechts | –
    - 10 reps / P: 0 s
- Air Squat | –
    - 15 reps / P: 0 s
- Glute Bridge | –
    - 15 reps / P: 0 s

Main | 45 min | Kernübungen für Bein- und Rumpfkraft mit progressiver Belastung und Fokus auf die Ziele.
- Back Squat | –
    - 10 reps @ 60 kg / P: 120 s
    - 5 reps @ 90 kg / P: 180 s
    - 5 reps @ 102.5 kg / P: 180 s
    - 5 reps @ 102.5 kg / P: 180 s
    - 5 reps @ 102.5 kg / P: 180 s
- Barbell Deadlift | –
    - 8 reps @ 80 kg / P: 120 s
    - 5 reps @ 110 kg / P: 180 s
    - 5 reps @ 122.5 kg / P: 180 s
    - 5 reps @ 122.5 kg / P: 180 s
    - 5 reps @ 122.5 kg / P: 180 s
- Bulgarian Split Squat with Dumbbells | –
    - 8 reps @ 20 kg / P: 90 s
    - 8 reps @ 20 kg / P: 90 s
    - 8 reps @ 22.5 kg / P: 90 s
    - 8 reps @ 22.5 kg / P: 90 s
    - 8 reps @ 22.5 kg / P: 90 s
    - 8 reps @ 22.5 kg / P: 90 s
- Barbell Hip Thrust | –
    - 10 reps @ 70 kg / P: 90 s
    - 10 reps @ 80 kg / P: 90 s
    - 10 reps @ 80 kg / P: 90 s
- Side Plank links | –
    - 45 s / P: 60 s
- Side Plank rechts | –
    - 45 s / P: 60 s
- Side Plank links | –
    - 45 s / P: 60 s
- Side Plank rechts | –
    - 45 s / P: 60 s

Cool-Down | 5 min | Förderung der Regeneration und Verbesserung der Flexibilität nach dem Training.
- Couch Stretch links | –
    - 60 s
- Couch Stretch rechts | –
    - 60 s
- Standing Pike Stretch | –
    - 60 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 