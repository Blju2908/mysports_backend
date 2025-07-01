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
      "position": 0,
      "exercises": [
        {
          "name": "Jumping Jacks",
          "position": 0,
          "sets": [
            {"values": [null, null, 60, null, null], "position": 0}
          ]
        },
        {
          "name": "Armkreisen",
          "position": 1,
          "sets": [
            {"values": [null, 10, null, null, null], "position": 0}
          ]
        }
      ]
    },
    {
      "name": "Hauptteil",
      "description": "Krafttraining Superset",
      "position": 1,
      "exercises": [
        {
          "name": "Kurzhantel Bankdrücken",
          "superset_id": "A",
          "position": 0,
          "sets": [
            {"values": [20, 12, null, null, 60], "position": 0},
            {"values": [20, 10, null, null, 60], "position": 1},
            {"values": [20, 8, null, null, 60], "position": 2}
          ]
        },
        {
          "name": "Kurzhantel Rudern",
          "superset_id": "A",
          "position": 1,
          "sets": [
            {"values": [20, 12, null, null, 0], "position": 0},
            {"values": [20, 10, null, null, 0], "position": 1},
            {"values": [20, 8, null, null, 0], "position": 2}
          ]
        }
      ]
    },
    {
      "name": "Cooldown",
      "description": "Dehnung und Entspannung",
      "position": 2,
      "exercises": [
        {
          "name": "Brustdehnung",
          "position": 0,
          "sets": [
            {"values": [null, null, 30, null, null], "position": 0}
          ]
        }
      ]
    }
  ]
}
```

# Input
Workout: Hyrox-Style Kraft & Hybrid (≈60 min | Fokus: Kraft, Ausdauer, Funktionalität)

Warm-Up | 7 min | Aktivierung und Mobilität für den ganzen Körper
- Jumping Jacks | –
    - 60 s / P: 30 s
- Dynamic Walking Lunges | –
    - 10 reps / P: 30 s
- Arm Circles | –
    - 10 reps / P: 15 s
    - 10 reps / P: 15 s
- Thoracic Spine Rotation (Quadruped) | –
    - 8 reps / P: 15 s
    - 8 reps / P: 15 s
- World's Greatest Stretch | –
    - 4 reps / P: 30 s
    - 4 reps / P: 30 s

Main | 48 min | Kraftaufbau im Oberkörperzug und Beine, Hyrox-inspirierter Zirkel und Rumpfstabilität
- Barbell Row | –
    - 8 @ 70 kg / P: 90 s
    - 6 @ 75 kg / P: 90 s
    - 5 @ 80 kg / P: 90 s
    - 5 @ 80 kg / P: 90 s
- Single-Arm Dumbbell Row | –
    - 8 @ 30 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
    - 8 @ 30 kg / P: 60 s
- Bulgarian Split Squat (Barbell) | –
    - 8 @ 35 kg / P: 75 s
    - 8 @ 35 kg / P: 75 s
    - 8 @ 35 kg / P: 75 s
    - 8 @ 35 kg / P: 75 s
    - 8 @ 35 kg / P: 75 s
    - 8 @ 35 kg / P: 75 s
- Ski Ergometer | A
    - 300 m / P: 15 s
    - 300 m / P: 15 s
    - 300 m / P: 15 s
- Sled Pull | B
    - 20 m / P: 15 s
    - 20 m / P: 15 s
    - 20 m / P: 15 s
- Farmers Carry (Dumbbell) | C
    - 40 m @ 30 kg / P: 15 s
    - 40 m @ 30 kg / P: 15 s
    - 40 m @ 30 kg / P: 15 s
- Wall Ball Shot | D
    - 15 reps / P: 15 s
    - 15 reps / P: 15 s
    - 15 reps / P: 15 s
- Burpee to Target | E
    - 10 reps / P: 90 s
    - 10 reps / P: 90 s
    - 10 reps / P: 90 s
- Plank Up-Down | –
    - 10 reps / P: 45 s
    - 10 reps / P: 45 s
    - 10 reps / P: 45 s
- Hollow Body Hold | –
    - 45 s / P: 45 s
    - 45 s / P: 45 s
    - 45 s / P: 45 s

Cool-Down | 5 min | Dehnung und Entspannung
- Hamstring Stretch (Seated Forward Fold) | –
    - 45 s / P: 15 s
- Couch Stretch | –
    - 45 s / P: 15 s
    - 45 s / P: 15 s
- Pigeon Pose (Forward) | –
    - 45 s / P: 15 s
    - 45 s / P: 15 s
- Child's Pose | –
    - 60 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 