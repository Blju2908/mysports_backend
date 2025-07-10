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
  - Für jede Muskelgruppe den Recovery-Status (Fresh/Moderate/Recent) nennen und kurz erläutern, wie Intensität und Volumen daraus abgeleitet wurden.
  - Keine Nutzerziele wiederholen; fokussiere auf Recovery-Insights, Equipment und Zeitbudget.
- Berechne alle Gewichtsvorgaben autoregulatorisch:
  - Erfolgreiche Performance (>48 h): +2,5–5 kg
  - Negative Notes/hohe Intensität: gleiches Gewicht
  - Neue Übung oder >3 Sessions Pause: –10 %
- Fasse Isolationsübungen, die nacheinander liegen, automatisch als Superset (ID A, B, …).
- Seitenübungen (Stretching, Unilateral) immer separat als 'links' und 'rechts' ausweisen.
- Bewegungsmusterspezifisches Warm-Up: Ergänze für den Session-Fokus passende Aktivierungsübungen (z.B. Push-Mobilisation für Push-Workouts).
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
...

<Cool-Down | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. '–'>
    - <Parameter Set 1>
...

<Tracking & Next | – | Kurzer Hinweis>
- Zu tracken: <Parameter, z.B. Gewicht, Reps, RPE>
- Nächste Session: <Erwartete Anpassung>
```
