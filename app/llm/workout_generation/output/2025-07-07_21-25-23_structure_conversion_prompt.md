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
Workout: Beine & Core Kraft (≈60 min | Fokus: Beine, Gesäß, Core)

Warm-Up | 10 min | Dynamische Mobilisierung für Unterkörper und Hüfte
- Jumping Jacks | –
    - 60 s
- Dynamic Walking Lunges | –
    - 10 reps
- Leg Swings Front-to-Back | A
    - A - Leg Swings Front-to-Back links: 10 reps
    - A - Leg Swings Front-to-Back rechts: 10 reps
- Leg Swings Side-to-Side | B
    - B - Leg Swings Side-to-Side links: 10 reps
    - B - Leg Swings Side-to-Side rechts: 10 reps
- 90/90 Hip Switch | –
    - 60 s
- Glute Bridge | –
    - 15 reps

Main | 45 min | Klassisches Krafttraining für Beine, Gesäß und Core
- Barbell Front Squat | –
    - 8 @ 60 kg / P: 90 s
    - 6 @ 65 kg / P: 90 s
    - 5 @ 70 kg / P: 120 s
    - 6 @ 65 kg / P: 90 s
- Barbell Romanian Deadlift | –
    - 8 @ 85 kg / P: 90 s
    - 8 @ 85 kg / P: 90 s
    - 10 @ 80 kg / P: 90 s
- Bulgarian Split Squat with Barbell | A
    - A - Bulgarian Split Squat with Barbell links: 8 @ 40 kg / P: 60 s
    - A - Bulgarian Split Squat with Barbell rechts: 8 @ 40 kg / P: 60 s
    - A - Bulgarian Split Squat with Barbell links: 8 @ 45 kg / P: 60 s
    - A - Bulgarian Split Squat with Barbell rechts: 8 @ 45 kg / P: 60 s
    - A - Bulgarian Split Squat with Barbell links: 8 @ 45 kg / P: 60 s
    - A - Bulgarian Split Squat with Barbell rechts: 8 @ 45 kg / P: 60 s
- Barbell Hip Thrust | –
    - 12 @ 65 kg / P: 75 s
    - 10 @ 70 kg / P: 75 s
    - 10 @ 70 kg / P: 75 s
- Hanging Leg Raise | –
    - 12 reps / P: 60 s
    - 12 reps / P: 60 s
    - 10 reps / P: 60 s
- Side Plank | B
    - B - Side Plank links: 40 s / P: 30 s
    - B - Side Plank rechts: 40 s / P: 30 s
    - B - Side Plank links: 40 s / P: 30 s
    - B - Side Plank rechts: 40 s / P: 30 s
    - B - Side Plank links: 35 s / P: 30 s
    - B - Side Plank rechts: 35 s / P: 30 s
- Standing Calf Raise Machine | –
    - 15 @ 40 kg / P: 60 s
    - 15 @ 40 kg / P: 60 s
    - 12 @ 40 kg / P: 60 s

Cool-Down | 5 min | Statisches Dehnen für Beine und Hüfte
- 90/90 Hip Switch | –
    - 60 s
- Hamstring Stretch (Standing) | A
    - A - Hamstring Stretch (Standing) links: 45 s
    - A - Hamstring Stretch (Standing) rechts: 45 s
- Hip Flexor Stretch (Kneeling) | B
    - B - Hip Flexor Stretch (Kneeling) links: 45 s
    - B - Hip Flexor Stretch (Kneeling) rechts: 45 s
- Calf Stretch Against Wall | C
    - C - Calf Stretch Against Wall links: 45 s
    - C - Calf Stretch Against Wall rechts: 45 s
- Child's Pose | –
    - 60 s

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 