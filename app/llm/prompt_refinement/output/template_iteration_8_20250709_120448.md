# Aufgabe
Erstelle ein herausragendes, personalisiertes Workout basierend auf den Trainingszielen, der Historie und der Recovery der letzten 7–14 Tage. Begründe in der Description Intensitäten, Übungsauswahl, Equipment und Zeitbudget. Verwende die folgenden Trainingsprinzipien:

{training_principles}

# Übungsbibliothek
{exercise_library}

# Validierung & Fallback
- Verwende ausschließlich Übungen aus {exercise_library}.
- Alle Übungsbezeichnungen müssen genau der Bibliothek entsprechen. Nicht-exakte Treffer: mappe über Synonym-Tabelle → kennzeichne mit ' [Mapped]'.
- Kann keine sichere Zuordnung getroffen werden: gib 'UNRESOLVED_EXERCISE: [OriginalName]' + Top 3 Alternativen.
- Jede gemappte oder ungelöste Übung muss ausdrücklich mit '[Mapped]' oder 'UNRESOLVED_EXERCISE' ausgezeichnet sein.

# Description
- Kurze Zusammenfassung: Warum dieses Setup?
- Für jede trainierte Muskelgruppe: Recovery-Status (Fresh/Moderate/Recent) → Herleitung von Intensität & Volumen.
- Nenne verwendetes Equipment (inkl. Studio- & Home-Equipment: Kettlebells, Widerstandsbänder, Pull-Up-Bar) und Gesamtzeitbudget.

# Autoregulative Gewichtsanpassung
Berechne vor jeder Übung das zu verwendende Gewicht:
1. Erste Durchführung einer Übung → Initiales Gewicht = 40 % des geschätzten 1RM (bei Freihanteln) oder 10 % des Körpergewichts (bei Kettlebells/Widerstandsbändern).
2. > 3 Sessions Pause seit letzter Durchführung → − 10 % des letzten Gewichts.
3. Erfolgreiche Performance + > 48 h Regeneration → + 2,5–5 kg.
4. Negative Notes oder < 48 h Regeneration → unverändert.

# Supersets
- Nur für direkt aufeinanderfolgende Isolationsübungen.
- Gemeinsame ID (A, B, …), gleiche Sätze & Wiederholungen.

# Warm-Up & Cool-Down
- Warm-Up: spezifisch zum Session-Fokus, keine irrelevanten Aktivierungen.
- Cool-Down: Fokus-spezifisches Dehnen oder Zirkel passend zum Session-Thema.

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