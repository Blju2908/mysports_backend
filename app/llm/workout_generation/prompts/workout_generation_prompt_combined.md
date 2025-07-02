# WICHTIGE ANWEISUNGEN
⚠️ KRITISCH: NIEMALS alle "values" als null setzen! Jeder Satz MUSS realistische Zahlen enthalten!

{training_principles}

# Übungsbibliothek
{exercise_library}

# Aufgabe
Erstelle das perfekte nächste Workout für den Nutzer und gib es direkt im JSON-Schema-Format zurück.

# JSON Schema Regeln

## ⚠️ KRITISCHE REGEL: NIEMALS ALLE NULL-WERTE!
**Das values Array MUSS immer EXAKT 5 Werte haben und relevante Felder MÜSSEN konkrete Zahlen enthalten!**

1. **Präzise Strukturierung**: Alle Informationen korrekt in das WorkoutSchema einordnen (name, description, duration, focus, blocks)

2. **Set-Parameter - KRITISCH**: Pro Satz EXAKT 5 Werte im Format: [Gewicht_kg, Wiederholungen, Dauer_sek, Distanz_m, Pause_sek]
   - **Kraftübungen**: [80, 8, null, null, 60] (Gewicht + Wiederholungen + Pause)
   - **Cardio/Zeit**: [null, null, 300, null, 30] (nur Dauer + Pause)
   - **Distanz**: [null, null, null, 1000, 60] (nur Distanz + Pause)
   - **Bodyweight**: [null, 12, null, null, 45] (nur Wiederholungen + Pause)
   - **Halteübungen**: [null, null, 45, null, 30] (nur Dauer + Pause)
   - Die Parameter müssen für jeden Satz korrekt eingegeben werden!!!

3. **Superset-IDs**: Verwende Buchstaben für die Bezeichnung von Supersets. (A, B, C, ...). Bitte stelle bei Supersets sicher, dass Du trotzdem alle Sätze zu einer Übung zusammenfasst. Durch die gegebene Superset-ID, werden die Sätze der Superset Übungen im Zirkel durchgeführt.

4. **Realistische Werte**: Setze angemessene Gewichte, Zeiten und Wiederholungen entsprechend der Trainingsziele des Users.

5. **Vollständigkeit**: Gib immer das gesamte Workout mit allen Blöcken aus

6. **ABSOLUT VERBOTEN**: Niemals alle 5 Werte als `null` setzen! Mindestens 1-2 Werte MÜSSEN konkrete Zahlen sein!
   - ❌ FALSCH: `[null, null, null, null, null]` 
   - ✅ RICHTIG: `[null, 12, null, null, 45]` oder `[80, 8, null, null, 60]`

7. **WICHTIG**: Bitte nutze das Position Attribut der jeweiligen Elemente, um festzulegen in welcher Reihenfolge die Blöcke, Exercises und Sets durchgeführt werden sollen.

# JSON-Spezifische Zusatzregeln
- Bitte versuche Circuit und HIIT Supersets in einem eigenen Block zu gruppieren.


# JSON Schema Beispiel
```json
{{
  "name": "Krafttraining Oberkörper",
  "description": "Vollständiges Krafttraining für den Oberkörper mit Warm-Up und Cooldown",
  "duration": 60,
  "focus": "Kraft, Oberkörper",
  "blocks": [
    {{
      "name": "Warm-Up",
      "description": "Dynamische Aufwärmung",
      "position": 0,
      "exercises": [
        {{
          "name": "Armkreisen",
          "position": 0,
          "sets": [
            {{"values": [null, 15, null, null, null], "position": 0}}
          ]
        }},
        {{
          "name": "Hüftkreisen",
          "position": 1,
          "sets": [
            {{"values": [null, 15, null, null, null], "position": 0}}
          ]
        }}
      ]
    }},
    {{
      "name": "Main",
      "description": "Krafttraining Superset",
      "position": 1,
      "exercises": [
        {{
          "name": "Push-up",
          "superset_id": "A",
          "position": 0,
          "sets": [
            {{"values": [null, 12, null, null, 45], "position": 0}},
            {{"values": [null, 10, null, null, 45], "position": 1}},
            {{"values": [null, 8, null, null, 60], "position": 2}}
          ]
        }},
        {{
          "name": "Pull-up an der Klimmzugstange",
          "superset_id": "A",
          "position": 1,
          "sets": [
            {{"values": [null, 8, null, null, 60], "position": 0}},
            {{"values": [null, 6, null, null, 60], "position": 1}},
            {{"values": [null, 5, null, null, 90], "position": 2}}
          ]
        }},
        {{
          "name": "Side Plank links",
          "superset_id": "B", // Das muss im gleichen Superset sein wie die Rechts-Seite. Es könnte aber auch alles im Superset A sein.
          "position": 2,
          "sets": [
            {{"values": [null, null, 30, null, null], "position": 0}},
            {{"values": [null, null, 30, null, null], "position": 1}}
          ]
        }},
        {{
          "name": "Side Plank rechts",
          "superset_id": "B", // Das muss im gleichen Superset sein wie die Links-Seite. Es könnte aber auch alles im Superset A sein.
          "position": 3,
          "sets": [
            {{"values": [null, null, 30, null, 60], "position": 0}},
            {{"values": [null, null, 30, null, 60], "position": 1}}
          ]
        }}
      ]
    }},
    {{
      "name": "Cool-Down",
      "description": "Dehnung und Entspannung",
      "position": 2,
      "exercises": [
        {{
          "name": "Butterfly Stretch",
          "position": 0,
          "sets": [
            {{"values": [null, null, 30, null, null], "position": 0}}
          ]
        }}
        ...
      ]
    }}
  ]
}}
```

# Input
Aktuelles Datum: {current_date}

User Prompt: {user_prompt}

Trainingsziele:
{training_plan}

Trainingshistorie:
{training_history}

# Output
Gib **ausschließlich** das vollständige Workout als korrektes JSON zurück, ohne Markdown oder zusätzliche Erklärungen. 
