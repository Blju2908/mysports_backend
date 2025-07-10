# Aufgabe
Deine Aufgabe ist es, ein herausragendes personalisiertes Workout zu erstellen. Analysiere die Recovery der letzten 7–14 Tage und begründe in der Description Intensitäten, Übungsauswahl, Equipment und Zeitbudget.

{training_principles}

# Übungsbibliothek
{exercise_library}

# Validierung & Fallback
- Vergleiche Übungsnamen exakt mit der Bibliothek.
- Mappe gängige Synonyme automatisch (z. B. 'Liegestütze' → 'Push-Up').
- Bei Mehrdeutigkeiten: wähle die bestpassende Übung und kennzeichne sie mit ' [Mapped]'.
- Kann keine sichere Zuordnung getroffen werden: markiere als 'UNRESOLVED_EXERCISE: [OriginalName]' und schlage die Top 3 Alternativen vor.

# Description
- Kurze Zusammenfassung: Warum dieses Setup?
- Für jede trainierte Muskelgruppe: Recovery-Status (Fresh / Moderate / Recent) → Ableitung von Intensität & Volumen.
- Nenne Equipment und Zeitbudget.

# Autoregulative Gewichtsanpassung
1. Neue Übung oder >3 Sessions Pause → −10 % vom letzten Gewicht.
2. Erfolgreiche Performance + >48 h Regeneration → +2,5–5 kg.
3. Negative Notes oder <48 h Regeneration → unverändert.

# Supersets
- Nur für direkt aufeinanderfolgende Isolationsübungen.
- Gemeinsame ID (A, B, …), gleiche Sätze & Wiederholungen.

# Warm-Up & Cool-Down
- Warm-Up: spezifisch zum Session-Fokus, keine irrelevanten Aktivierungen.
- Cool-Down: Dehnung/Zirkel passend zum Fokus.

# Parameterformat
- Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
- Wiederholungen: `15 reps`
- Dauer: `60 s`
- Distanz: `300 m`
- Pause: `P: x s`

# Ausgabeformat
Gib ausschließlich den Workout-Text im exakt vorgegebenen Format zurück, ohne zusätzlichen Freitext.

Format-Beispiel:
```
Workout: Oberkörper Push (≈60 min | Fokus: Brust, Schultern, Trizeps | Description: ...)

<Warm-Up | 8 min | Schulter- und Brustmobilisation>
- Shoulder Pass-Through with Resistance Band | –
    - 15 reps / P: 30 s

<Main | 45 min | Schwere Grundübungen + Isolationssupersets>
- Barbell Bench Press | –
    - 5 @ 80 kg / P: 120 s
- Dumbbell Shoulder Press | –
    - 4 @ 22.5 kg / P: 90 s
- Triceps Pushdown (Cable Machine) | A
    - 12 @ 30 kg / P: 60 s
- Overhead Triceps Extension (Cable Machine) | A
    - 12 @ 30 kg / P: 60 s

<Cool-Down | 7 min | Dehnung Brust/Schultern>
- Doorway Stretch | –
    - 60 s per side

<Tracking & Next | – | Kurzer Hinweis>
- Zu tracken: Gewicht, Reps, Pause, subjektives RPE
- Nächste Session: Gewicht +2.5 kg auf Bench Press wenn RPE ≤7
``` 

# Input
Aktuelles Datum: {current_date}

User Prompt: {user_prompt}

Trainingsziele:
{training_plan}

Trainingshistorie:
{training_history}
