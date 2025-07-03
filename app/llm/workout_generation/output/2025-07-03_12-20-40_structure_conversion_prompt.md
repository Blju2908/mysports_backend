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
Workout: Kraft & Hyrox-Stil Hybrid (≈60 min | Fokus: Kraft, Ausdauer, Ästhetik)

Warm-Up | 10 min | Dynamische Mobilisierung und Herz-Kreislauf-Vorbereitung
- Jumping Jacks | –
    - 60 s / P: 30 s
- World's Greatest Stretch | –
    - 5 reps pro Seite / P: 30 s
- Cat-Cow Flow | –
    - 10 reps / P: 30 s
- Leg Swings Front-to-Back | –
    - 10 reps pro Seite / P: 30 s

Main | 45 min | Steigerung von Kraft, funktionaler Ausdauer und Ästhetik
- Konventionelles Kreuzheben | –
    - 5 @ 90 kg / P: 120 s
    - 5 @ 125 kg / P: 150 s
    - 5 @ 125 kg / P: 150 s
    - 5 @ 125 kg / P: 150 s
- Pull-up an der Klimmzugstange | –
    - 8 reps / P: 90 s
    - 8 reps / P: 90 s
    - 7 reps / P: 90 s
- T-Bar Rudern mit Langhantel (Landmine-Aufsatz) | –
    - 10 @ 40 kg / P: 75 s
    - 10 @ 45 kg / P: 75 s
    - 10 @ 45 kg / P: 75 s
- Ski Ergometer | A
    - 200 m / P: 30 s
- Sled Push | A
    - 20 m @ 70 kg / P: 30 s
- Farmers Carry mit Kurzhanteln | A
    - 20 m @ 20 kg / P: 30 s
- Wall Ball Shot | A
    - 10 reps @ 9 kg / P: 90 s
- Ski Ergometer | A
    - 200 m / P: 30 s
- Sled Push | A
    - 20 m @ 70 kg / P: 30 s
- Farmers Carry mit Kurzhanteln | A
    - 20 m @ 20 kg / P: 30 s
- Wall Ball Shot | A
    - 10 reps @ 9 kg / P: 90 s
- Ski Ergometer | A
    - 200 m / P: 30 s
- Sled Push | A
    - 20 m @ 70 kg / P: 30 s
- Farmers Carry mit Kurzhanteln | A
    - 20 m @ 20 kg / P: 30 s
- Wall Ball Shot | A
    - 10 reps @ 9 kg / P: 90 s

Cool-Down | 5 min | Statisches Dehnen zur Förderung der Regeneration
- Liegende Wirbelsäulen-Drehung | –
    - 30 s pro Seite / P: 15 s
- Hamstring Stretch im Stehen | –
    - 30 s pro Seite / P: 15 s
- Knie-zur-Brust-Stretch | –
    - 30 s pro Seite / P: 15 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 