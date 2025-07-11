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
Workout: Lower Body Foundation & Core (≈60 min | Fokus: Beine, Glutes, Core, funktionelle Kraft | Description: Unterkörper komplett regeneriert, alle Beinmuskeln >5 Tage ohne Hauptreiz. Front Squats zuletzt mit schwer gefallen notiert – heute leichter und technisch sauber, Fokus auf Quad/Hüft-Mobilität und unilateralem Ausgleich, kombiniert mit Core für funktionelle Performance. Volumenbalanced, kein überlappendes Pull/Push, klare Progression für Unterkörper.)

Warm-Up | 10 min | Gelenk-Mobilität, Rumpfaktivierung, Bewegungsvorbereitung
- Arm Circles | –
    - 15 reps / P: 15 s
    - 15 reps / P: 15 s
- Inchworm Walkout | –
    - 8 reps / P: 30 s
- 90/90 Hip Switch | –
    - 10 reps / P: 20 s
- Dynamic Walking Lunges [unilateral] | A
    - 10 reps (links) / P: 0 s
    - 10 reps (rechts) / P: 40 s

Main | 43 min | Quadrizeps & Glutes Schwerpunkteinheit, unilateral ausbalanciert, Core gezielt eingebaut, Stretchpausen
- Barbell Front Squat | –
    - 8 @ 60 kg / P: 120 s
    - 6 @ 75 kg / P: 150 s
    - 6 @ 75 kg / P: 150 s
    - 6 @ 75 kg / P: 150 s
- Bulgarian Split Squat with Dumbbells (links) | B
    - 10 @ 18 kg / P: 0 s
    - 10 @ 18 kg / P: 0 s
    - 10 @ 18 kg / P: 0 s
- Bulgarian Split Squat with Dumbbells (rechts) | B
    - 10 @ 18 kg / P: 60 s
    - 10 @ 18 kg / P: 60 s
    - 10 @ 18 kg / P: 120 s
- Barbell Romanian Deadlift | –
    - 10 @ 70 kg / P: 90 s
    - 10 @ 70 kg / P: 90 s
    - 10 @ 70 kg / P: 120 s
- Single-Leg Calf Raise (links) | C
    - 12 reps / P: 0 s
    - 12 reps / P: 0 s
- Single-Leg Calf Raise (rechts) | C
    - 12 reps / P: 40 s
    - 12 reps / P: 90 s
- Plank Hold | –
    - 60 s / P: 60 s
    - 45 s / P: 60 s
    - 45 s / P: 90 s

Cool-Down | 7 min | Beweglichkeit, Stretching Full Lower Body, Erholung fördern
- Hamstring Stretch (Standing) (links) | D
    - 30 s / P: 0 s
- Hamstring Stretch (Standing) (rechts) | D
    - 30 s / P: 10 s
- Couch Stretch (links) | E
    - 30 s / P: 0 s
- Couch Stretch (rechts) | E
    - 30 s / P: 10 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 