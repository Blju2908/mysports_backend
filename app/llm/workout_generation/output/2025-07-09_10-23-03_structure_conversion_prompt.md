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
Workout: Push Day – Kraft & Ästhetik (≈60 min | Fokus: Brust, Schultern, Trizeps | Description: Fokus auf Brust, Schultern und Trizeps für maximale Kraftentwicklung und Ästhetik. Hohe Intensität in Grundübungen nach optimaler Regeneration der Druckmuskulatur. Ergänzt durch Assistenz- und Isolationsübungen für umfassendes Muskelwachstum.)

Warm-Up | 10 min | Mobilisierung der Schultern und Aktivierung der Druckmuskulatur zur Vorbereitung auf schwere Lifts.
- Arm Circles | –
    - 15 reps / P: 0 s
    - 15 reps / P: 0 s
- Shoulder Pass-Through with Resistance Band | –
    - 12 reps / P: 0 s
    - 12 reps / P: 0 s
- Push-up | –
    - 10 reps / P: 0 s
    - 10 reps / P: 60 s

Main | 45 min | Klassische Kraftübungen zur Steigerung der Maximalkraft und Muskelhypertrophie.
- Barbell Bench Press | –
    - 8 @ 70 kg / P: 120 s
    - 6 @ 72.5 kg / P: 150 s
    - 6 @ 75 kg / P: 180 s
    - 5 @ 77.5 kg / P: 180 s
- Strict Barbell Overhead Press | –
    - 6 @ 40 kg / P: 120 s
    - 5 @ 42.5 kg / P: 150 s
    - 5 @ 45 kg / P: 150 s
- Dumbbell Incline Bench Press | –
    - 10 @ 25 kg / P: 90 s
    - 8 @ 27.5 kg / P: 90 s
    - 8 @ 27.5 kg / P: 90 s
- Lateral Raise with Dumbbells | –
    - 12 @ 10 kg / P: 60 s
    - 12 @ 10 kg / P: 60 s
    - 10 @ 12.5 kg / P: 60 s
- Cable Triceps Push-down with Straight Bar | –
    - 12 @ 20 kg / P: 60 s
    - 10 @ 22.5 kg / P: 60 s
    - 10 @ 22.5 kg / P: 60 s
- Overhead Triceps Extension with Dumbbell links | A
    - 12 @ 10 kg / P: 60 s
    - 10 @ 12.5 kg / P: 60 s
- Overhead Triceps Extension with Dumbbell rechts | A
    - 12 @ 10 kg / P: 120 s
    - 10 @ 12.5 kg / P: 120 s

Cool-Down | 5 min | Dehnung der beanspruchten Muskelgruppen zur Förderung der Flexibilität und Regeneration.
- Doorway Pec Stretch | –
    - 30 s / P: 0 s
- Triceps Overhead Stretch links | –
    - 30 s / P: 0 s
- Triceps Overhead Stretch rechts | –
    - 30 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 