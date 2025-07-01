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
Workout: Hyrox-Style Push & Core Power (≈60 min | Fokus: Kraft, Ästhetik, Hyrox-Ausdauer)

Warm-Up | 8 min | Aktivierung und Mobilisierung
- Armkreisen | –
    - 15 reps vorwärts / P: 0 s
    - 15 reps rückwärts / P: 0 s
- Cat-Cow Flow | –
    - 10 reps / P: 0 s
- World's Greatest Stretch | –
    - 5 reps pro Seite / P: 0 s
- Inchworm Walkout | –
    - 8 reps / P: 0 s

Main | 47 min | Kraftentwicklung und Hyrox-spezifische Ausdauer
- Schrägbankdrücken mit Langhantel | –
    - 10 @ 40 kg / P: 90 s
    - 8 @ 55 kg / P: 90 s
    - 6 @ 65 kg / P: 120 s
    - 6 @ 65 kg / P: 120 s
- Striktes Schulterdrücken mit Langhantel | –
    - 8 @ 35 kg / P: 75 s
    - 6 @ 45 kg / P: 90 s
    - 5 @ 50 kg / P: 90 s
- Dips an den Ringen | –
    - 8 reps / P: 60 s
    - 8 reps / P: 60 s
    - 7 reps / P: 60 s
- Trizepsdrücken am Kabelzug mit Seil | –
    - 12 @ 20 kg / P: 45 s
    - 12 @ 25 kg / P: 45 s
    - 10 @ 30 kg / P: 45 s
- Ski Ergometer | A1
    - 250 m / P: 30 s
    - 250 m / P: 30 s
    - 250 m / P: 30 s
- Wall Ball Shot | A2
    - 15 reps / P: 30 s
    - 15 reps / P: 30 s
    - 15 reps / P: 30 s
- Sled Push | A3
    - 20 m @ 80 kg / P: 30 s
    - 20 m @ 80 kg / P: 30 s
    - 20 m @ 80 kg / P: 30 s
- Burpee | A4
    - 10 reps / P: 90 s
    - 10 reps / P: 90 s
    - 10 reps / P: 90 s
- Plank Hold | –
    - 60 s / P: 45 s
    - 60 s / P: 45 s
    - 60 s / P: 45 s
- Leg Raise | –
    - 15 reps / P: 45 s
    - 15 reps / P: 45 s
    - 15 reps / P: 45 s

Cool-Down | 5 min | Dehnung und Regeneration
- Cross-Body Schulterdehnung | –
    - 30 s pro Seite / P: 0 s
- Türrahmen-Brustdehnung | –
    - 45 s / P: 0 s
- Kindhaltung | –
    - 60 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 