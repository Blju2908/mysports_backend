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
Workout: Push Power & Aesthetics (≈55 min | Fokus: Brust, Schultern, Trizeps | Description: Dieses Workout konzentriert sich auf Kraft- und Muskelaufbau für die Brust, Schultern und den Trizeps. Basierend auf deiner Trainingshistorie sind diese Muskelgruppen optimal erholt und bereit für eine intensive Belastung nach den letzten Pull- und Hyrox-Einheiten. Die Übungsauswahl und Gewichtsplanung fördern progressive Überlastung und eine ausgewogene Entwicklung.)

Warm-Up | 10 min | Vorbereitung der oberen Körpermuskulatur und Gelenke auf die Belastung
- Arm Circles | –
    - 15 reps
    - 15 reps
- Shoulder Pass-Through with Resistance Band | –
    - 12 reps
    - 12 reps
- Push-up | –
    - 10 reps
    - 10 reps
- Cat-Cow Flow | –
    - 10 reps
    - 10 reps

Main | 40 min | Kraft- und Muskelaufbau für Brust, Schultern und Trizeps
- Barbell Bench Press | –
    - 6 @ 72.5 kg / P: 120 s
    - 6 @ 72.5 kg / P: 120 s
    - 6 @ 72.5 kg / P: 120 s
    - 6 @ 72.5 kg / P: 120 s
- Strict Barbell Overhead Press | –
    - 8 @ 45 kg / P: 120 s
    - 8 @ 45 kg / P: 120 s
    - 8 @ 45 kg / P: 120 s
    - 8 @ 45 kg / P: 120 s
- Dumbbell Incline Bench Press | –
    - 10 @ 27.5 kg / P: 90 s
    - 10 @ 27.5 kg / P: 90 s
    - 10 @ 27.5 kg / P: 90 s
- Lateral Raise with Dumbbells | –
    - 12 @ 12 kg / P: 60 s
    - 12 @ 12 kg / P: 60 s
    - 12 @ 12 kg / P: 60 s
- Cable Triceps Push-down with Straight Bar | –
    - 12 @ 35 kg / P: 60 s
    - 12 @ 35 kg / P: 60 s
    - 12 @ 35 kg / P: 60 s
- Dumbbell Skullcrusher | –
    - 12 @ 12.5 kg / P: 60 s
    - 12 @ 12.5 kg / P: 60 s
    - 12 @ 12.5 kg / P: 60 s

Cool-Down | 5 min | Dehnung der beanspruchten Muskelgruppen zur Förderung der Regeneration
- Doorway Pec Stretch | –
    - 60 s
- Cross-Body Shoulder Stretch [unilateral] | –
    - 30 s
    - 30 s
- Triceps Overhead Stretch [unilateral] | –
    - 30 s
    - 30 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 