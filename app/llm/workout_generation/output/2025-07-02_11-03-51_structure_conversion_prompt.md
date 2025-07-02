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
Workout: Kraft & Hyrox-Hybrid Oberkörper (≈60 min | Fokus: Kraft, Ausdauer, Ästhetik)

Warm-Up | 10 min | Mobilisierung & Aktivierung
- Jumping Jacks | –
    - 60 s / P: 15 s
    - 60 s / P: 15 s
- World's Greatest Hip Opener | –
    - 5 reps per side / P: 30 s
- Cat-Cow Flow | –
    - 10 reps / P: 30 s
- Shoulder Pass-Through mit PVC-Stange | –
    - 10 reps / P: 0 s

Main | 45 min | Oberkörper Kraft & Hyrox-Zirkel
- Schrägbankdrücken mit Kurzhantel | –
    - 8 @ 22.5 kg / P: 90 s
    - 6 @ 25 kg / P: 90 s
    - 5 @ 27.5 kg / P: 90 s
    - 5 @ 27.5 kg / P: 120 s
- Pull-up an der Klimmzugstange | –
    - 8 reps / P: 90 s
    - 6 reps / P: 90 s
    - 5 reps / P: 90 s
    - 5 reps / P: 120 s
- Striktes Schulterdrücken mit Kurzhanteln | –
    - 8 @ 17.5 kg / P: 75 s
    - 6 @ 20 kg / P: 75 s
    - 6 @ 20 kg / P: 90 s
- Ski Ergometer | A
    - 250 m / P: 0 s
- Wall Ball Shot | A
    - 15 reps @ 9 kg / P: 0 s
- Sled Push | A
    - 20 m @ 60 kg / P: 0 s
- Burpee to Target | A
    - 8 reps / P: 0 s
- Plank Up-Down | A
    - 10 reps / P: 90 s
- Ski Ergometer | A
    - 250 m / P: 0 s
- Wall Ball Shot | A
    - 15 reps @ 9 kg / P: 0 s
- Sled Push | A
    - 20 m @ 60 kg / P: 0 s
- Burpee to Target | A
    - 8 reps / P: 0 s
- Plank Up-Down | A
    - 10 reps / P: 90 s

Cool-Down | 5 min | Dehnung & Regeneration
- Liegende Wirbelsäulen-Drehung links | –
    - 60 s / P: 0 s
- Liegende Wirbelsäulen-Drehung rechts | –
    - 60 s / P: 30 s
- Taubenpose (Forward) links | –
    - 60 s / P: 0 s
- Taubenpose (Forward) rechts | –
    - 60 s / P: 30 s
- Cross-Body Schulterdehnung links | –
    - 30 s / P: 0 s
- Cross-Body Schulterdehnung rechts | –
    - 30 s / P: 0 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 