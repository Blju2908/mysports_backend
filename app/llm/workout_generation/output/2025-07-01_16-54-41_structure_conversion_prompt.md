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
Workout: Kraft & Hyrox-Style Konditionierung (≈60 min | Fokus: Kraft, Ausdauer, Funktionalität)

Warm-Up | 10 Minuten | Mobilisierung und Aktivierung für den gesamten Körper
- Jumping Jacks | –
    - 60 s / P: 30 s
- Armkreisen | –
    - 10 reps (vorwärts) / P: 15 s
    - 10 reps (rückwärts) / P: 15 s
- World's Greatest Stretch | –
    - 5 reps pro Seite / P: 30 s
- Cat-Cow Flow | –
    - 8 reps / P: 30 s

Main | 45 Minuten | Aufbau von Kraft und Verbesserung der Hyrox-spezifischen Ausdauer
- Striktes Schulterdrücken mit Langhantel | –
    - 8 @ 40 kg / P: 120 s
    - 6 @ 50 kg / P: 120 s
    - 5 @ 55 kg / P: 120 s
    - 5 @ 60 kg / P: 120 s
- Brustgestütztes Rudern an der Maschine | –
    - 12 @ 40 kg / P: 90 s
    - 10 @ 45 kg / P: 90 s
    - 10 @ 50 kg / P: 90 s
- Bulgarischer Split Squat mit Kurzhanteln | –
    - 10 @ 12.5 kg (links) / P: 60 s
    - 10 @ 12.5 kg (rechts) / P: 60 s
    - 10 @ 15 kg (links) / P: 60 s
    - 10 @ 15 kg (rechts) / P: 60 s
    - 8 @ 17.5 kg (links) / P: 60 s
    - 8 @ 17.5 kg (rechts) / P: 60 s
- Ski Ergometer | A
    - 300 m / P: 15 s
- Sled Pull | B
    - 20 m / P: 15 s
- Farmers Walk mit Kurzhanteln | C
    - 40 m @ 22.5 kg / P: 15 s
- Burpee | D
    - 10 reps / P: 15 s
- Plank Up-Down | E
    - 10 reps / P: 120 s
- Ski Ergometer | A
    - 300 m / P: 15 s
- Sled Pull | B
    - 20 m / P: 15 s
- Farmers Walk mit Kurzhanteln | C
    - 40 m @ 22.5 kg / P: 15 s
- Burpee | D
    - 10 reps / P: 15 s
- Plank Up-Down | E
    - 10 reps / P: 120 s
- Ski Ergometer | A
    - 300 m / P: 15 s
- Sled Pull | B
    - 20 m / P: 15 s
- Farmers Walk mit Kurzhanteln | C
    - 40 m @ 22.5 kg / P: 15 s
- Burpee | D
    - 10 reps / P: 15 s
- Plank Up-Down | E
    - 10 reps / P: 120 s

Cool-Down | 5 Minuten | Dehnung und Entspannung zur Förderung der Regeneration
- Kniender Hüftbeuger-Stretch | –
    - 30 s pro Seite / P: 10 s
- Cross-Body Schulterdehnung | –
    - 30 s pro Seite / P: 10 s
- Kindhaltung | –
    - 60 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 