# Aufgabe
Konvertiere den folgenden freien Workout-Revisions-Text in das exakte JSON-Schema-Format. Du bist ein Datenparser für überarbeitete Workouts.

# Regeln
1. **Präzise Strukturierung**: Extrahiere alle Informationen und mappe sie korrekt
2. **Schema-Konformität**: Folge exakt dem WorkoutSchema (name, description, duration, focus, blocks)
3. **Set-Parameter**: Pro Satz: [Gewicht_kg, Wiederholungen, Dauer_sek, Distanz_m, Pause_sek] - nutze `null` für nicht relevante Werte. Achte darauf, dass die Parameter an den richtigen Stellen eingesetzt werden!!!
4. **Superset-IDs**: Übernehme gleiche IDs (A, B, C) für gruppierte Übungen
5. **Realistische Werte**: Behalte alle Gewichte, Zeiten und Wiederholungen bei
6. **Keine Null-Bytes**: Verwende niemals Null-Bytes oder andere ungültige Zeichen
7. **Vollständigkeit**: Gib immer das gesamte Workout aus!
8. **Änderungen berücksichtigen**: Integriere alle beschriebenen Änderungen aus der Revision
9. **Coach-Statement ignorieren**: Die `Coach-Statement:`-Zeile am Anfang des Inputs wird ignoriert und nicht in das JSON übernommen.

Parameternotation des Inputs:
- Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
- Wiederholungen: `15 reps`
- Dauer: `60 s`
- Dauer und Gewicht: `60 s @ 80 kg`
- Distanz: `300 m`
- Pause: `... / P: 60 s` --> Pause in Sekunden


# Vollständiges Workout-Beispiel
(Beispiel für Warm-Up, Hauptteil und Cool-Down)
```json
{
  "name": "Krafttraining Oberkörper (Revision)",
  "description": "Überarbeitetes Krafttraining für den Oberkörper einschließlich Warm-Up und Cool-Down",
  "duration": 60,
  "focus": "Kraft, Oberkörper",
  "blocks": [
    {
      "name": "Warm-Up",
      "description": "Dynamische Aufwärmung",
      "position": 0,
      "exercises": [
        {
          "name": "Jumping Jacks",
          "position": 0,
          "sets": [
            {"values": [null, null, 60, null, null], "position": 0}
          ],
          "superset_id": null
        },
        {
          "name": "Armkreisen",
          "position": 1,
          "sets": [
            {"values": [null, 10, null, null, null], "position": 0}
          ],
          "superset_id": null
        }
      ]
    },
    {
      "name": "Hauptteil",
      "description": "Krafttraining Superset",
      "position": 1,
      "exercises": [
        {
          "name": "Kurzhantel Bankdrücken",
          "superset_id": "A",
          "position": 0,
          "sets": [
            {"values": [20, 12, null, null, 60], "position": 0},
            {"values": [20, 10, null, null, 60], "position": 1},
            {"values": [20, 8, null, null, 60], "position": 2}
          ]
        },
        {
          "name": "Kurzhantel Rudern links",
          "superset_id": "A",
          "position": 1,
          "sets": [
            {"values": [20, 12, null, null, 0], "position": 0},
            {"values": [20, 10, null, null, 0], "position": 1},
            {"values": [20, 8, null, null, 0], "position": 2}
          ]
        },
        {
          "name": "Kurzhantel Rudern rechts",
          "superset_id": "A",
          "position": 2,
          "sets": [
            {"values": [20, 12, null, null, 0], "position": 0},
            {"values": [20, 10, null, null, 0], "position": 1},
            {"values": [20, 8, null, null, 0], "position": 2}
          ]
        }
      ]
    },
    {
      "name": "Cooldown",
      "description": "Dehnung und Entspannung",
      "position": 2,
      "exercises": [
        {
          "name": "Brustdehnung",
          "position": 0,
          "sets": [
            {"values": [null, null, 30, null, null], "position": 0}
          ],
          "superset_id": null
        }
      ]
    }
  ]
}
```

# Input
```
{freeform_revision}
```

# Ausgabe
Ausschließlich korrektes JSON ohne Markdown oder zusätzliche Erklärungen. 