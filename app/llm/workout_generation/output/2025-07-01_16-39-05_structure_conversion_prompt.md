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
Workout: Oberkörper Kraft & Hyrox Ausdauer (≈60 min | Fokus: Kraft, Ästhetik, Hyrox)

Warm-Up | 10 min | Vorbereitung auf Oberkörper & Ganzkörperbewegung
- Jumping Jacks | –
    - 60 s
- Dynamic Walking Lunges | –
    - 10 reps / P: 0 s
- Arm Circles | –
    - 10 reps (vorwärts) / P: 0 s
    - 10 reps (rückwärts) / P: 0 s
- World's Greatest Stretch | –
    - 5 reps (pro Seite) / P: 0 s

Main | 45 min | Steigerung von Oberkörperkraft & Ausdauerzirkel
- Incline Bench Press | –
    - 8 @ 40 kg / P: 90 s
    - 6 @ 50 kg / P: 90 s
    - 5 @ 55 kg / P: 120 s
    - 5 @ 60 kg / P: 120 s
- Barbell Row | –
    - 8 @ 40 kg / P: 90 s
    - 6 @ 50 kg / P: 90 s
    - 5 @ 55 kg / P: 120 s
    - 5 @ 60 kg / P: 120 s
- Strict Overhead Press | –
    - 8 @ 25 kg / P: 75 s
    - 6 @ 30 kg / P: 75 s
    - 5 @ 35 kg / P: 90 s
    - 5 @ 40 kg / P: 90 s
- Barbell Curl | –
    - 10 @ 25 kg / P: 60 s
    - 10 @ 27.5 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
- Cable Triceps Push-down | –
    - 12 @ 20 kg / P: 60 s
    - 12 @ 22.5 kg / P: 60 s
    - 10 @ 25 kg / P: 60 s
- Ski Ergometer | A
    - 250 m / P: 0 s
- Sled Pull | A
    - 20 m / P: 0 s
- Farmer's Carry (Dumbbell) | A
    - 30 m @ 22.5 kg / P: 0 s
- Wall Ball Shot | A
    - 12 reps / P: 90 s
- Ski Ergometer | A
    - 250 m / P: 0 s
- Sled Pull | A
    - 20 m / P: 0 s
- Farmer's Carry (Dumbbell) | A
    - 30 m @ 22.5 kg / P: 0 s
- Wall Ball Shot | A
    - 12 reps / P: 90 s
- Ski Ergometer | A
    - 250 m / P: 0 s
- Sled Pull | A
    - 20 m / P: 0 s
- Farmer's Carry (Dumbbell) | A
    - 30 m @ 22.5 kg / P: 0 s
- Wall Ball Shot | A
    - 12 reps / P: 90 s

Cool-Down | 5 min | Regeneration & Flexibilität
- Doorway Pec Stretch | –
    - 30 s (pro Seite)
- Child's Pose | –
    - 60 s
- Triceps Overhead Stretch | –
    - 30 s (pro Seite)

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 