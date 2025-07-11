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
Workout: Home Strength Session (≈45 min | Fokus: Full Body, Strength, Conditioning | Description: Intelligente Übungsauswahl. Turkish Get Ups als Kernelement. Maximale Nutzung verfügbarer Kettlebells und Klimmzugstange. Vollständiges körperliches Training. Optimiert für Muskelwachstum und Kraftsteigerung.)

Warm-Up | 5 Minuten | Aufwärmübungen zur Mobilisation und Aktivierung
- Arm Circles | –
    - 15 reps
    - 15 reps
- Jumping Jacks | –
    - 60 s

Main | 35 Minuten | Fokus auf grundlegenden Krafttraining mit Kettlebell und Körpergewicht
- Turkish Get-Up rechts | A
    - 5 reps @ 24 kg / P: 60 s
    - 5 reps @ 24 kg / P: 60 s
- Turkish Get-Up links | A
    - 5 reps @ 24 kg / P: 60 s
    - 5 reps @ 24 kg / P: 60 s
- Pull-up | –
    - 6 reps / P: 120 s
    - 5 reps / P: 120 s
    - 4 reps / P: 120 s
- Kettlebell Swing | –
    - 12 reps @ 24 kg / P: 90 s
    - 12 reps @ 24 kg / P: 90 s
    - 12 reps @ 24 kg / P: 90 s
- Push-up | B
    - 15 reps / P: 60 s
    - 12 reps / P: 60 s
- Dumbbell Farmer's Carry | B
    - 20 m @ 24 kg / P: 60 s
    - 20 m @ 24 kg / P: 60 s

Cool-Down | 5 Minuten | Dehnübungen zur Erholung
- Child's Pose | –
    - 60 s
- Downward Dog | –
    - 60 s

```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 