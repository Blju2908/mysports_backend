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
Workout: Calisthenics & Band Strength (≈60 min | Fokus: Ganzkörper, Funktionelle Kraft | Description: Aufbauend auf Push/Hypertrophy Fokus. Band- sowie Calisthenics-übungen. Optimierung funktionelle Kraft & Core-Stabilität.)

Warm-Up | 10 Minuten | Gelenke mobilisieren und Ganzkörper vorbereiten
- Arm Circles | –
    - 15 reps
    - 15 reps
- Inchworm Walkout | –
    - 5 reps
    - 5 reps
- Jumping Jacks | –
    - 60 s
- Band Pull-Aparts | –
    - 15 reps
    - 15 reps

Main | 45 Minuten | Ganzkörper Kraftaufbau & Core-Stabilität
- Archer Pull-up on Pull-up Bar | –
    - 4 reps
    - 4 reps
    - 4 reps
- Pseudo Planche Push-up | –
    - 8 reps
    - 8 reps
    - 8 reps
- Bulgarian Split Squat with Resistance Band links | A
    - 10 reps
    - 10 reps
- Bulgarian Split Squat with Resistance Band rechts | A
    - 10 reps
    - 10 reps
- Hollow Body Hold | –
    - 30 s
    - 30 s
    - 30 s
- Resistance Band Woodchoppers links | B
    - 12 reps
    - 12 reps
- Resistance Band Woodchoppers rechts | B
    - 12 reps
    - 12 reps
- Ring Dip | –
    - 6 reps
    - 6 reps
    - 6 reps
- Plank Up-Down | –
    - 10 reps
    - 10 reps

Cool-Down | 5 Minuten | Fördert Erholung und Flexibilität
- Child's Pose | –
    - 60 s
- Doorway Pec Stretch | –
    - 30 s
- Lying Glute Stretch links | –
    - 30 s
- Lying Glute Stretch rechts | –
    - 30 s
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 