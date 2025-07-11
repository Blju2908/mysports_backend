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
Workout: Athletic Lower Body Strength & Core (≈60 min | Fokus: Unterkörper, Glute-Balance, Core, Progression | Description: Frische Beine nach 6 Tagen – daher intensive, progressive Lower-Body-Session. Kniebeuge- und Glute-Push zur Steigerung funktioneller Kraft, Bewegungsausgleich durch Hip Thrust. Isolierte Unilateralität für Side-Balance, Core zwischengeschaltet. Stretching-Pausen im Block für Regeneration und Beweglichkeits-Boost.)

Warm-Up | 10 min | Mobilisation und Aktivierung Unterkörper & Core, Vorbereitung auf schwere Grundübungen
- Jumping Jacks | –
    - 45 s 
- Air Squat | –
    - 15 reps
- Dynamic Walking Lunges [unilateral] | A
    - 8 reps (links)
    - 8 reps (rechts)
- Inchworm Walkout | –
    - 8 reps
- Hip Circles | –
    - 10 reps

Main | 42 min | Progressives Kraft-/Hypertrophie-Volumen für Beine/Glutes, Core-Integration, Stretch Pausen
- Barbell Back Squat | –
    - 7 @ 95 kg / P: 150 s
    - 7 @ 95 kg / P: 150 s
    - 6 @ 100 kg / P: 180 s
    - 6 @ 100 kg / P: 180 s
- Barbell Romanian Deadlift | –
    - 10 @ 80 kg / P: 120 s
    - 10 @ 80 kg / P: 120 s
    - 8 @ 90 kg / P: 120 s
- Barbell Hip Thrust | –
    - 12 @ 100 kg / P: 120 s
    - 10 @ 110 kg / P: 120 s
    - 8 @ 120 kg / P: 120 s
- Bulgarian Split Squat with Dumbbells (links) | B
    - 10 @ 22 kg / P: 0 s
    - 8 @ 22 kg / P: 0 s
- Bulgarian Split Squat with Dumbbells (rechts) | B
    - 10 @ 22 kg / P: 90 s
    - 8 @ 22 kg / P: 90 s
- Plank Hold | –
    - 60 s / P: 60 s
    - 45 s / P: 60 s
- Hamstring Stretch (Standing) (links) | C
    - 30 s / P: 0 s
- Hamstring Stretch (Standing) (rechts) | C
    - 30 s / P: 90 s
- Couch Stretch (links) | D
    - 30 s / P: 0 s
- Couch Stretch (rechts) | D
    - 30 s / P: 90 s

Cool-Down | 8 min | Regeneration, Mobilität Fokus Hüfte & Beuge, entspannter Abschluss
- Pigeon Pose (links) | –
    - 40 s
- Pigeon Pose (rechts) | –
    - 40 s
- Figure-4 Stretch (Seated) (links) | –
    - 40 s
- Figure-4 Stretch (Seated) (rechts) | –
    - 40 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 