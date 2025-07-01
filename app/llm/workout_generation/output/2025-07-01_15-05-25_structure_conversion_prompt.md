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
Workout: Kraft & Funktionale Ausdauer Zuhause (≈60 min | Fokus: Kraft, Hyrox-Stil, Funktionell)

Warm-Up | 10 Minuten | Mobilisierung & Aktivierung
- Cat-Cow Flow | –
    - 60 s
- Hüftkreisen | –
    - 30 s (links) / P: 0 s
    - 30 s (rechts) / P: 0 s
- Armkreisen | –
    - 10 reps vorwärts / P: 0 s
    - 10 reps rückwärts / P: 0 s
- Dynamische Ausfallschritte | –
    - 8 reps pro Bein / P: 0 s

Main | 48 Minuten | Kraft & Hyrox-inspirierter Zirkel
- Kettlebell Swing (Russian) | –
    - 15 reps @ 24 kg / P: 90 s
    - 18 reps @ 24 kg / P: 90 s
    - 20 reps @ 24 kg / P: 90 s
    - 20 reps @ 24 kg / P: 90 s
- Pull-up an der Klimmzugstange | –
    - 8 reps / P: 90 s
    - 8 reps / P: 90 s
    - 7 reps / P: 90 s
    - 6 reps / P: 90 s
- Kettlebell Clean einarmig | –
    - 8 reps @ 24 kg (links) / P: 60 s
    - 8 reps @ 24 kg (rechts) / P: 60 s
    - 8 reps @ 24 kg (links) / P: 60 s
    - 8 reps @ 24 kg (rechts) / P: 60 s
    - 8 reps @ 24 kg (links) / P: 60 s
    - 8 reps @ 24 kg (rechts) / P: 60 s
- Push-up | –
    - 15 reps / P: 60 s
    - 15 reps / P: 60 s
    - 12 reps / P: 60 s
- Einbeiniger Hip Thrust | –
    - 12 reps (links) / P: 45 s
    - 12 reps (rechts) / P: 45 s
    - 12 reps (links) / P: 45 s
    - 12 reps (rechts) / P: 45 s
    - 10 reps (links) / P: 45 s
    - 10 reps (rechts) / P: 45 s
- Suitcase Carry (links) | A
    - 30 s @ 24 kg / P: 0 s
    - 30 s @ 24 kg / P: 0 s
    - 30 s @ 24 kg / P: 0 s
- Suitcase Carry (rechts) | A
    - 30 s @ 24 kg / P: 0 s
    - 30 s @ 24 kg / P: 0 s
    - 30 s @ 24 kg / P: 0 s
- Burpee Broad Jump | A
    - 5 reps / P: 0 s
    - 5 reps / P: 0 s
    - 5 reps / P: 0 s
- Mountain Climber | A
    - 45 s / P: 0 s
    - 45 s / P: 0 s
    - 45 s / P: 0 s
- Plank Hold | A
    - 60 s / P: 120 s
    - 60 s / P: 120 s
    - 60 s / P: 0 s

Cool-Down | 7 Minuten | Dehnung & Entspannung
- Butterfly Stretch | –
    - 60 s / P: 0 s
- Stehende Vorwärtsbeuge | –
    - 60 s / P: 0 s
- Bretzel Stretch | –
    - 60 s (links) / P: 0 s
    - 60 s (rechts) / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 