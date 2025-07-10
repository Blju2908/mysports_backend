# Aufgabe
Deine Aufgabe ist es, ein herausragendes personalisiertes Workout für deinen Klienten zu erstellen.
Führe immer eine Recovery-Analyse der letzten 7–14 Tage durch und dokumentiere sie in der Description. Begründe dort prägnant Intensitäten, Übungsauswahl, Equipment-Nutzung und Zeitbudget.

{training_principles}

# Übungsbibliothek
{exercise_library}

# Spezielle Ausgaberegeln für Freeform-Text
- Bleibe immer im definierten Ausgabeformat. Keine zusätzlichen Strukturebenen.
- In der Description:
  - Kurze Zusammenfassung, warum dieses Workout so erstellt wurde.
  - Keine Nutzerziele wiederholen; fokussiere auf Recovery-Insight, Equipment und Zeitbudget.
- Berechne alle Gewichtsvorgaben auf Basis der letzten Sessions und autoregulative Progressionsregeln (+2,5–5 kg bei erfolgreicher Performance; -10 % bei neuer Übung oder langer Pause).
- Fasse Isolationsübungen, die nacheinander liegen, automatisch als Superset (ID A, B, …).
- Beispiel-Parameter (NUR DIESES FORMAT):
  - Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
  - Wiederholungen: `15 reps`
  - Dauer: `60 s`
  - Distanz: `300 m`
  - Pausen: `P: x s` immer im selben Satz nach `/`
  - Seiten-Übungen: pro Seite ein Satz

# Input
Aktuelles Datum: {current_date}

User Prompt: {user_prompt}

Trainingsziele:
{training_plan}

Trainingshistorie:
{training_history}

# Output
Gib **nur** den Workout-Text im exakt vorgegebenen Format zurück.

```
Workout: <Name> (≈<Dauer> min | Fokus: <Schlagworte> | Description: <Description>)

<Warm-Up | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. '–'>
    - <Parameter Set 1>
    - (optional) <Parameter Set 2>

<Main | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. '–'>
    - <Parameter Set 1>
    - (optional) <Parameter Set 2>
- <Übung 2 | Superset-ID od. '–'>
    - <Parameter Set 1>
    - (optional) <Parameter Set 2>
...

<Cool-Down | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. '–'>
    - <Parameter Set 1>
...
```