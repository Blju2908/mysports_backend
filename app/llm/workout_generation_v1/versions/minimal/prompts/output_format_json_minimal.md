# 📤 Final Instruction & Output Format

**IMPORTANT**: Your entire response MUST be a single, valid JSON object and nothing else. The content must be in **GERMAN**, though exercise names can be in English.

## Exaktes JSON-Ausgabeformat
Gib das Workout in folgendem minimalen JSON-Format zurück. Halte dich exakt an die Struktur und die Feldnamen.

- **Keine Einheiten** in den JSON-Werten
- **Nur Name und Anzahl Sets** pro Übung
- **Einfache, klare Struktur** für Performance-Optimierung

```json
{
  "name": "Home Kettlebell & Pull-Up Bar HIIT",
  "focus": "Kraft, Muskelaufbau",
  "blocks": [
    {
      "name": "Warm-Up",
      "exercises": [
        {
          "name": "Jumping Jacks",
          "sets": 2
        },
        {
          "name": "Arm Circles",
          "sets": 2
        },
        {
          "name": "Dynamic Walking Lunges",
          "sets": 2
        }
      ]
    },
    {
      "name": "Main",
      "exercises": [
        {
          "name": "Russian Kettlebell Swing",
          "sets": 4
        },
        {
          "name": "Pull-up",
          "sets": 4
        },
        {
          "name": "Single-Arm Kettlebell Clean",
          "sets": 3
        },
        {
          "name": "Burpee",
          "sets": 3
        },
        {
          "name": "Plank Hold",
          "sets": 3
        }
      ]
    },
    {
      "name": "Cool-Down",
      "exercises": [
        {
          "name": "Child's Pose",
          "sets": 1
        },
        {
          "name": "Doorway Pec Stretch",
          "sets": 1
        }
      ]
    }
  ]
}
```

## Wichtige Regeln:
1. **name**: Prägnanter Workout-Name (max. 5 Wörter)
2. **focus**: Kurze Beschreibung des Workout-Fokus (max. 10 Wörter)
3. **blocks**: Genau 3 Blöcke: "Warm-Up", "Main", "Cool-Down"
4. **exercises**: Liste der Übungen mit Name und Anzahl Sets
5. **sets**: Einfache Ganzzahl für die Anzahl der Sets

Gib NUR das JSON-Objekt zurück, keine zusätzlichen Erklärungen oder Text.