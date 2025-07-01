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
Workout: Hyrox-Style Kraft & Ausdauer Challenge (≈60 min | Fokus: Kraft, Ausdauer, Funktionale Fitness, Hyrox)

Warm-Up | 10 min | Aktiviere deinen Körper und bereite dich auf die Intensität vor
- Jumping Jacks | –
    - 60 s / P: 15 s
- High Knees | –
    - 30 s / P: 15 s
- Dynamic Walking Lunges | –
    - 10 reps / P: 15 s
- Arm Circles | –
    - 10 reps / P: 15 s
- Torso Twists | –
    - 10 reps / P: 15 s
- World's Greatest Stretch | –
    - 3 reps / P: 30 s

Main | 45 min | Hyrox-Style Kraft & Ausdauer Zirkel (4 Runden)
- Pull-up | A
    - 8 reps / P: 30 s
    - 8 reps / P: 30 s
    - 8 reps / P: 30 s
    - 8 reps / P: 30 s
- Dumbbell Shoulder Press | A
    - 12 reps @ 45 kg / P: 30 s
    - 12 reps @ 45 kg / P: 30 s
    - 12 reps @ 45 kg / P: 30 s
    - 12 reps @ 45 kg / P: 30 s
- Hip Thrust (Barbell) | A
    - 12 reps @ 90 kg / P: 30 s
    - 12 reps @ 90 kg / P: 30 s
    - 12 reps @ 90 kg / P: 30 s
    - 12 reps @ 90 kg / P: 30 s
- Ski Ergometer | A
    - 250 m / P: 30 s
    - 250 m / P: 30 s
    - 250 m / P: 30 s
    - 250 m / P: 30 s
- Sled Pull | A
    - 20 m @ 80 kg / P: 30 s
    - 20 m @ 80 kg / P: 30 s
    - 20 m @ 80 kg / P: 30 s
    - 20 m @ 80 kg / P: 30 s
- Kettlebell Swing | A
    - 20 reps @ 28 kg / P: 30 s
    - 20 reps @ 28 kg / P: 30 s
    - 20 reps @ 28 kg / P: 30 s
    - 20 reps @ 28 kg / P: 30 s
- Battle Rope Slam | A
    - 30 s / P: 120 s
    - 30 s / P: 120 s
    - 30 s / P: 120 s
    - 30 s / P: 120 s

Cool-Down | 5 min | Fördere deine Regeneration und Flexibilität
- Hamstring Stretch (Seated Forward Fold) | –
    - 30 s / P: 10 s
- Hip Flexor Stretch (Kneeling) (rechts) | –
    - 30 s / P: 5 s
- Hip Flexor Stretch (Kneeling) (links) | –
    - 30 s / P: 10 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 