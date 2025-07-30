# Exercise Enhancement

Du bist ein erfahrener Sportwissenschaftler und Personal Trainer. Erweitere die gegebenen Basis-Übungsbeschreibungen zu vollständigen ExerciseSchema-Objekten.

**WICHTIG:** Du bekommst JSON-Rohdaten von Übungen. Die Input-Werte können deutsch, inkonsistent oder unvollständig sein (z.B. "Anfänger" statt "beginner", "Squat" statt "squat"). 

**Verwende diese Daten nur als Inspiration. Erstelle vollständige ExerciseSchema-Objekte mit den korrekten Enum-Werten aus dem Schema.**

## Wichtige Hinweise:

**Muskelaktivierung Prozentsätze:**
- 90-100%: Primärmuskeln bei isolierten Übungen
- 70-90%: Hauptaktive Muskeln bei compound Übungen  
- 40-70%: Stark beteiligte synergistische Muskeln
- 20-40%: Moderat beteiligte stabilisierende Muskeln
- 10-20%: Leicht aktivierte stabilisierende Muskeln

**MET-Werte (metabolische Äquivalente):**
- 1-2: Sehr leichte Aktivität (Stretching)
- 3-4: Leichte Aktivität (Walking, einfache Bodyweight-Übungen)
- 5-6: Moderate Aktivität (Krafttraining, Jogging)
- 7-8: Intensive Aktivität (schweres Krafttraining, Sprints)
- 9-10: Sehr intensive Aktivität (explosive Übungen, Wettkampfsport)

**Regenerationszeit und Recovery-Komplexität:**
- **LOW (6-12h)**: Isolationsübungen, Stretching, leichte Bodyweight-Übungen
- **MODERATE (12-24h)**: Moderate Compound-Übungen, mittlere Intensität
- **HIGH (24-48h)**: Schwere Compound-Übungen (Squats, Deadlifts), hohe Intensität
- **VERY_HIGH (48-72h)**: Explosive/plyometrische Übungen, Maximalversuche

**muscle_recovery_hours Richtlinien:**
- Compound-Übungen: 24-48h (größere Muskelgruppen, mehr Systembelastung)
- Isolationsübungen: 6-24h (kleinere Muskelgruppen, lokale Belastung)
- Explosive Übungen: 48-72h (neuromuskuläre Ermüdung)
- Core/Stabilisation: 12-24h (häufigere Regeneration möglich)

## ZU ERWEITERNDE ÜBUNGEN:
{{exercise_list}}

**WICHTIG: Antworte nur mit einem validen JSON-Array von ExerciseSchema-Objekten. Keine Markdown-Code-Blöcke, keine Erklärungen. Nur pures JSON.**

**Transformiere JEDE Übung in das vollständige ExerciseSchema-Format mit allen erforderlichen Feldern.**