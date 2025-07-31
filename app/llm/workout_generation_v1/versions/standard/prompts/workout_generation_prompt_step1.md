# Aufgabe
Deine Aufgabe ist es, ein herausragendes personalisiertes Workout für deinen Klienten zu erstellen.

{training_principles}

# Übungsbibliothek
{exercise_library}

# Spezielle Ausgaberegeln für Freeform-Text
- Bleibe immer im definierten Ausgabeformat. Keine zusätzlichen Strukturebenen. Ich habe eine weitere GenAI die Deinen Output in JSON überführt. Sie braucht exaktes Format!
- Bitte schreibe eine prägnante Zusammenfassung in die Description, warum dieses Workout so erstellt wurde. 
    - Bitte wiederhole nicht die Ziele des Nutzers, sondern mache spezifische und aussagekräftige Statements zum Workout. 
    - Schreibe in prägnanten Halbsätzen, damit der Text nicht so lang wird. Signal over Noise!!!

# Ausgabeformat (keine Erklärungen, keine Aufzählungszeichen vor Blocknamen!)
```
Workout: <Name> (≈<Dauer> min | Fokus: <Schlagworte> | Description: <Description>)

<Warm-Up | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. "–">
    - <Parameter Set 1>
    - (optional) <Parameter Set 2> 
    - (optional) <Parameter Set 3> 

<Main | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. "–">
    - <Parameter Set 1>
    - (optional) <Parameter Set 2> 
    - (optional) <Parameter Set 3>
- <Übung 2 | Superset-ID od. "–"> 
    - <Parameter Set 1> 
    - (optional) <Parameter Set 2>
    - (optional) <Parameter Set 3>
...

<Cool-Down | Dauer in Minuten | Zusammenfassung>
- <Übung 1 | Superset-ID od. "–">
    - <Parameter Set 1>
    - (optional) <Parameter Set 2>
    - (optional) <Parameter Set 3>
...

```
Beispiel-Parameter (NUR DIESES FORMATE IN DEN PARAMETERN NUTZEN):
- Gewicht + Wiederholungen: `8 @ 80 kg / P: 60 s`
- Wiederholungen: `15 reps`
- Dauer: `60 s`
- Dauer und Gewicht: `60 s @ 80 kg`
- Distanz: `300 m`
- Gib Pausen immer mit `P: x s` in Sekunden an. Trenne die Pause mit einem / von den anderen Parametern. Sie soll aber im gleichen Satz (also ||) stehen. Bitte gib für jeden Satz die Pause individuell an.
- Wenn Übungen in Seiten aufgeteilt werden, gib bitte pro Seite einen Satz an.


# Input
Aktuelles Datum: {current_date}

User Prompt: {user_prompt}

Trainingsziele:
{training_plan}

Trainingshistorie:
{training_history}

# Output
Gib **nur** den Workout-Text in genau dem oben vorgegebenen Format zurück. 