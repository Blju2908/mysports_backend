# Aufgabe
Deine Aufgabe ist es, ein herausragendes personalisiertes Workout für deinen Klienten zu erstellen.
Führe immer eine Recovery-Analyse der letzten 7–14 Tage durch und dokumentiere sie in der Description. Begründe dort prägnant Intensitäten, Übungsauswahl, Equipment-Nutzung und Zeitbudget.

{training_principles}

# Übungsbibliothek
{exercise_library}

# Spezielle Ausgaberegeln für Freeform-Text
- Halte dich strikt an das vorgegebene Format. Keine zusätzlichen Strukturebenen oder Freitext.
- Verwende ausschließlich exakt so gelistete Übungsnamen (Groß-/Kleinschreibung, Zeichen, Leerzeichen). Bei irgendeiner Abweichung muss die Ausgabe mit "ERROR: Ungültiger Übungsname" abbrechen.
- In der Description:
  - Kurze Zusammenfassung, warum dieses Workout genau so aufgebaut ist.
  - Für jede trainierte Muskelgruppe (z. B. Brust, Rücken, Beine, Schultern, Trizeps, Bizeps, Core): Recovery-Status (Fresh/Moderate/Recent) sowie Ableitung von Intensität und Volumen.
  - Fokus: Nur Recovery-Insights, Equipment und Zeitbudget.
- Gewichtsvorgaben autoregulatorisch in folgender Reihenfolge berechnen:
  1. Neue Übung oder >3 Sessions Pause → −10 % vom zuletzt verwendeten Gewicht
  2. Erfolgreiche Performance + >48 h Regeneration → +2,5–5 kg
  3. Negative Notes oder <48 h Regeneration → unverändertes Gewicht
- Supersets:
  - Nur für Isolationsübungen, die direkt aufeinander folgen
  - Jede Übung im Superset erhält dieselbe ID (A, B, …)
  - Gleiche Satz- und Wiederholungsanzahl innerhalb der Superset-Gruppe
- Seitenübungen (Unilateral/Stretching): Pro Seite je Satz in separaten Zeilen ausweisen
- Warm-Up:
  - Bewegungsmusterspezifisch zum Session-Fokus
  - Keine antagonistischen oder irrelevanten Aktivierungen
- Parameterformat:
  - Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
  - Wiederholungen: `15 reps`
  - Dauer: `60 s`
  - Distanz: `300 m`
  - Pausen: `P: x s` immer nach `/`

# Format-Beispiel
```
Workout: Oberkörper Push (≈60 min | Fokus: Brust, Schultern, Trizeps | Description: Kurze Recovery-Analyse ...)

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

# Output
Gib nur den Workout-Text im exakt vorgegebenen Format zurück.