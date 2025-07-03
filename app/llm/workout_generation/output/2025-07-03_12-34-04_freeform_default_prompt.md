# Aufgabe
Deine Aufgabe ist es, ein herausragendes personalisiertes Workout für deinen Klienten zu erstellen.

# 🏋️ Trainingsprinzipien & Kernanweisungen

## Rolle & Mission
Du bist ein Weltklasse-Personal-Trainer und Ernährungscoach. Du bist hochmotiviert dem Nutzer die perfekte Trainingserfahrung zu bieten.

## WICHTIGE GRUNDREGEL
- **Erstelle das Workout ausschließlich mit Übungen aus der untenstehenden Übungsbibliothek.**
- **EQUIPMENT-REGEL**: Nutze NUR Übungen, die mit dem verfügbaren Equipment und der Umgebung des Users funktionieren!
    - Bei Home-Workouts: Nur explizit verfügbare Equipment verwenden
    - Kein Equipment angegeben: Ausschließlich Bodyweight-Übungen
    - Gym-Workouts: Alle Equipment-Optionen verfügbar

## Nutzungskontext
- Nutze die Trainingsziele vom Nutzer, um das Workout zu definieren
- Nutze die Trainingshistorie für realistische Parameter
- Verwende das aktuelle Datum, um die Regeneration des Users abzuschätzen

## Kernprinzipien der Trainingsplanung
1. **Zielgerichtete Blockstruktur**: Definiere Blöcke die zu den Zielen des Nutzers passen
2. **Progressive Belastungssteuerung**: Baue eine geeignete progressive Belastungssteuerung ein
3. **Ausgewogene Übungsauswahl**: Nutze eine ausgewogene Übungsauswahl, ohne Muskelgruppen zu überlasten
4. **Stilgerechtes Training**: Baue ein Workout im Stil des Wunsches vom Nutzer
5. **Zeitoptimierung**: Achte darauf, dass das Workout die zur Verfügung stehende Zeit möglichst optimal trifft
    - Krafttraining: ca. 6 Übungen mit 3-4 Sets pro Übung pro Stunde
    - Bei 45 min: ca. 4 Übungen mit 3-4 Sets pro Übung
6. **Sinnvoller Split**: Wähle einen sinnvollen Split basierend auf der Anzahl der Sessions pro Woche des Users
7. **Equipment-Compliance**: Achte bei Home-Workouts darauf, nur die explizit zur Verfügung stehenden Equipments zu nutzen

## Übungsauswahl & Formatierungsregeln
- **Exakte Übungsnamen**: Nutze nur die Übungen aus der Übungsbibliothek und übernehme die EXAKTEN Namen der Übungen. Füge nichts zu den Übungsnamen hinzu!
- **Asynchrone Übungen**: Bei Übungen die seitenspezifisch oder asymmetrisch ausgeführt werden (z.B. Side Plank, Single Leg Deadlift):
    - Erstelle ZWEI separate Exercises (z.B. "Side Plank links" und "Side Plank rechts")
    - Gruppiere beide Exercises IMMER im gleichen Superset (z.B. beide mit superset_id "A")
    - Verteile die Sätze entsprechend auf beide Exercises
- **Supersets & Circuits**: Gruppiere Übungen bei Bedarf als Superset mit `A`, `B`, `C` …
    - Wichtig für HIIT und Circuits: Alle Übungen die im Zirkel ausgeführt werden sollen, müssen in einem Superset zusammengefasst werden
    - Nutze Supersets nur, wenn die gleichen Übungen mehrfach hintereinander ausgeführt werden sollen
- **Geschützte Begriffe**: Vermeide geschützte Begriffe (z.B. "Crossfit", "Hyrox")
- **Gewichtsangaben**: 
    - Gib bei Übungen für das Gym immer ein Gewicht an! Mache eine konservative Schätzung für User ohne Historie
    - Bei Dumbbell-Übungen immer das Gewicht von einer Hantel angeben (22,5kg und nicht 45kg!)

## Pausenregelung
- **Keine Extra-Pausenübungen**: Bitte keine Extra Übungen für Pausen einfügen
- **Pausennotation**: Wenn nach einer Übung eine Pause gemacht werden soll, in der definierten Notation machen
- **Individuelle Pausenangaben**: Gib für jeden Satz die Pause individuell an

## Satz-Strukturierung
- **Einzelsatz-Beschreibung**: Beschreibe jede Satzzeile einzeln - Pro Satz eine Zeile mit denselben Spalten (NICHT 4x 12 @ 80 kg)
- **Relevante Parameter**: Verwende nur relevante Parameter pro Satz (Reps × Gewicht, Dauer, Distanz, Pause)
- **Seitenspezifische Sätze**: Wenn Übungen in Seiten aufgeteilt werden, gib pro Seite einen Satz an 

# Übungsbibliothek
# Verfügbare Übungen

- 90/90 Hip Switch
- Adductor Rock Back
- Advanced Tuck Planche
- Agility-Leiter In-In-Out-Out
- Air Squat
- Alternierender Kurzhantel Clean & Jerk
- Ankle Bounces
- Ankle Dorsiflexion Stretch
- Archer Pull-up an Klimmzugstange
- Archer Push-up
- Archer-Rudern an den Ringen
- Armkreisen
- Arnold-Press
- Assault Bike
- Aufrechtes Rudern am Kabelzug
- Aufrechtes Rudern mit Kurzhanteln
- Aufrechtes Rudern mit Langhantel
- Aufschauender Hund
- Ausfallschritt mit Gewichtsscheibe über Kopf
- Ausfallschritt mit Langhantel
- Ausfallschritt rückwärts
- Ausfallschritt vorwärts
- Back Lever Hold an Klimmzugstange
- Back Lever Hold an Ringen
- Band Distraction Hip Opener
- Bankdip mit erhöhten Füßen
- Bankdrücken an der Smith Machine
- Bankdrücken mit Kurzhanteln
- Bankdrücken mit Langhantel
- Bar Dip an Dipstangen
- Battle Rope Slam
- Battle Rope Wave
- Bear Crawl
- Bear Crawl Drag mit Kettlebell
- Beinpresse
- Bird Dog Reach
- Bizepscurl am Kabelzug mit Seil
- Bizepscurl am Kabelzug mit Stange
- Box Jump Over
- Box Jump Step Down
- Box Squat an der Smith Machine
- Box Squat mit Langhantel
- Bretzel Stretch
- Brustgestütztes Rudern an der Maschine
- Brustgestütztes Rudern mit Kurzhanteln
- Bulgarischer Split Squat einbeinig
- Bulgarischer Split Squat mit Kurzhanteln
- Bulgarischer Split Squat mit Langhantel
- Burpee
- Burpee Broad Jump
- Burpee to Target
- Butt Kicks
- Butterfly Stretch
- Cable Fly am Kabelzug
- Calf Stretch Against Wall
- Cat-Cow Flow
- Chin-up an der Klimmzugstange
- Chin-up mit Gym-Maschine
- Clapping Pull-up an der Klimmzugstange
- Clutch Flag an der Klimmzugstange
- Commando Pull-up an der Klimmzugstange
- Couch-Stretch
- Crab Walk
- Cross-Body Schulterdehnung
- Curtsy Lunge
- Dead Hang
- Decline Push-up
- Decline-Bankdrücken mit Kurzhanteln
- Decline-Bankdrücken mit Langhantel
- Deficit-Kreuzheben mit Langhantel
- Devil's Press mit Kurzhanteln
- Diamond Push-up
- Dips an den Ringen
- Donkey Kick
- Double Under mit Springseil
- Downward Dog to Cobra
- Dragon Flag auf dem Boden
- Dragon Flag auf der Flachbank
- Dual Kettlebell Front Rack Carry
- Dumbbell Snatch
- Dynamische Ausfallschritte
- EZ-Stangen-Bizepscurls
- Einarmiger Klimmzug
- Einarmiger Liegestütz
- Einarmiges Kurzhantelrudern
- Einbeinige Glute Bridge
- Einbeiniger Hip Thrust
- Einbeiniges Wadenheben an der Stufe
- Enge Bankdrücken an der Smith Machine
- Enger Latzug am Kabelzug
- Enges Bankdrücken mit Langhantel
- Face Pull am Kabelzug
- Fahrrad-Crunch
- Farmers Carry mit Kettlebells
- Farmers Walk mit Kurzhanteln
- Figure-4-Dehnung im Sitzen
- Fire Hydrant
- Flutter Kick
- Frog Stretch
- Front Lever Hold an Gym-Ringen
- Front Lever Hold an der Klimmzugstange
- Front Lever Pull an Gym-Ringen
- Front Lever Pull an der Klimmzugstange
- Front Raise mit Kurzhantel
- Front Raise mit Langhantel
- Front Squat an der Smith Machine
- Front Squat mit Langhantel
- Full Planche auf Parallettes
- Full Planche auf dem Boden
- Gehende Ausfallschritte mit Langhantel
- Glute Bridge
- Good Morning an der Smith Machine
- Good Morning mit Langhantel
- Ground-to-Overhead mit Gewichtsscheibe
- Hack Squat an der Gym-Maschine
- Half Burpee
- Hammer Curl am Kabelzug
- Hammer Curl mit Kurzhantel
- Hamstring Stretch im Stehen
- Hand-Release Push-up
- Handgelenkbeuger-Dehnung auf der Bank
- Handstand Hold gegen Wand
- Handstand Push-up gegen Wand
- Handstand Walking auf dem Boden
- Handstand gegen die Wand
- Happy Baby Pose
- Heel Drop
- Herabschauender Hund
- High Knees
- Hindu Push-up
- Hip Thrust mit Langhantel
- Hollow Body Hold
- Hollow Rock
- Human Flag an einem vertikalen Pfosten
- Hüftkreisen
- Inchworm Walkout
- Incline Push-up an Bank
- Jefferson Curl mit Kurzhantel
- Jefferson Curl mit Langhantel
- Jump Squat
- Jumping Jacks
- Jumping Lunge
- Katzenbuckel
- Kettlebell Clean beidarmig
- Kettlebell Clean einarmig
- Kettlebell Snatch beidarmig
- Kettlebell Snatch einarmig
- Kettlebell Swing (American)
- Kettlebell Swing (Russian)
- Kindhaltung
- Klatschende Liegestütze
- Knie-zur-Brust-Stretch
- Kniebeuge in der Smith Machine
- Kniebeuge mit Langhantel
- Kniender Hüftbeuger-Stretch
- Kniender Quadrizeps-Stretch
- Konventionelles Kreuzheben
- Korean Dip
- Kossackhocke-Statik
- Kreuz-Bergsteiger
- Kreuzheben mit Langhantel
- Krähe
- Kuhhaltung
- Kurzhantel-Bizepscurls
- Kurzhantel-Brustfliegen
- Kurzhantel-Schulterdrücken
- L-Sit
- Landmine Press
- Landmine Rotational Press
- Landmine Row
- Landmine Squat-to-Press
- Langhantelcurl
- Lat Pulldown am Kabelzug
- Lateral Lunge
- Lateral Shuffle
- Leg Raise
- Leg Swings Front-to-Back
- Leg Swings Side-to-Side
- Liegende Wirbelsäulen-Drehung
- Liegender Gluteus-Stretch
- Liegestütze an den Ringen
- Lizard Pose
- Maltese Push-up auf Parallettes
- Meadows Row
- Medicine Ball Chest Pass
- Medicine Ball Slam
- Mountain Climber
- Muscle-up an den Ringen
- Muscle-up an der Turnstange
- Nacken-Seitdehnung
- Nackenbeuge-Dehnung
- Nackenpressen mit Langhantel
- Nackenstreckung
- Neutral-Grip Pull-up an der Parallelgriffstange
- One-Arm Chin-up an der Klimmzugstange
- Overhead Squat mit Langhantel
- Overhead-Trizepsdrücken am Kabelzug
- Paused Back Squat
- Paused Bankdrücken mit Langhantel
- Paused Kurzhantel-Bankdrücken
- Paused Smith-Machine-Bankdrücken
- Pike-Liegestütz auf Box
- Pistol Squat
- Planche Push-up auf Parallettes
- Plank Hold
- Plank Up-Down
- Preacher Curl mit EZ-Stange
- Preacher Curl mit Kurzhantel
- Press to Handstand an der Wand
- Pseudo Planche Push-up auf Parallettes
- Pull-up an der Klimmzugstange
- Push Press mit Kurzhantel
- Push Press mit Langhantel
- Push-up
- Reverse Pec Deck
- Ring Archer Push-up
- Ring Dip an Ringen
- Romanian Deadlift mit Kurzhantel
- Romanian Deadlift mit Langhantel
- Rope Trizepsstrecken am Kabelzug
- Rotation der Brustwirbelsäule im Vierfüßlerstand
- Row Sprint
- Ruderergometer
- Rudern am Kabelzug mit V-Griff
- Rudern am Kabelzug mit geradem Griff
- Rudern an den Ringen
- Ruderzugmaschine
- Russian Twist
- Safety Bar Squat
- Sandbag Front Carry
- Sandbag Shouldered Carry
- Sandbag Walking Lunge
- Schrägbankcurl am Kabelzug
- Schrägbankcurl mit Kurzhantel
- Schrägbankdrücken an der Smith Machine
- Schrägbankdrücken mit Kurzhantel
- Schrägbankdrücken mit Langhantel
- Schulterdislokation mit PVC-Stange
- Schulterdislokation mit Widerstandsband
- Schulterkontakt-Liegestütz
- Seal Jack
- Seal Row mit Langhantel
- Seitheben am Kabelzug
- Seitheben mit Kurzhanteln
- Seitlicher Boxsprung
- Seitlicher Hürdensprung
- Seitstütz
- Shoulder Pass-Through mit PVC-Stange
- Shoulder Pass-Through mit Widerstandsband
- Shrug mit Langhantel
- Single Under mit Springseil
- Sitzende Grätsche
- Sitzendes Pike-Pulsieren
- Sitzendes Trizepsdrücken mit Kurzhantel
- Ski Ergometer
- Skin-the-Cat an den Ringen
- Skorpion-Dehnung
- Skullcrusher mit Kurzhanteln
- Skullcrusher mit SZ-Stange
- Sled Pull
- Sled Push
- Sleeper-Stretch
- Speed Skater Hop
- Spider-Lunge mit Rotation
- Spiderman Liegestütz
- Split Squat
- Sprint
- Standweitsprung
- Star Jump
- Stehende Handgelenkbeuger-Dehnung
- Stehende IT-Band-Dehnung
- Stehende Vorwärtsbeuge
- Stehender Quadrizeps-Stretch
- Stehendes Wadenheben an der Maschine
- Steifes Kreuzheben mit Kurzhanteln
- Steifes Kreuzheben mit Langhantel
- Step-Up
- Step-Up auf Box
- Step-Up mit Kurzhanteln
- Straddle Planche auf Parallettes
- Straddle Planche auf dem Boden
- Straddle-Backlever an den Ringen
- Straddle-Frontlever an den Ringen
- Straight-Arm Pulldown am Kabelzug
- Striktes Schulterdrücken an der Smith Machine
- Striktes Schulterdrücken mit Kurzhanteln
- Striktes Schulterdrücken mit Langhantel
- Suitcase Carry mit Kettlebell
- Suitcase Carry mit Kurzhantel
- Sumo-Kreuzheben mit Langhantel
- Superman
- T-Bar Rudern mit Langhantel (Landmine-Aufsatz)
- Taubenpose (Forward)
- Thorakale Extension über die Schaumstoffrolle
- Thread-the-Needle
- Tire Flip
- Tire Jump-In Jump-Out
- Torso Twists
- Trap Bar Kreuzheben
- Trizeps-Dips an der Bank
- Trizeps-Overhead-Stretch
- Trizepsdrücken am Kabelzug mit Seil
- Trizepsdrücken am Kabelzug mit Stange
- Tuck Jump
- Tuck Planche auf Parallettes
- Tuck Planche auf dem Boden
- Typewriter Pull-up
- Türrahmen-Brustdehnung
- Umgekehrte Plank-Dips
- Umgekehrtes Crunch
- Umgekehrtes Plank
- Unterarmrücken-Dehnung
- V-Sit
- V-Up
- Vorgebeugtes Langhantelrudern
- Waden-Dehnung an der Wand
- Wadenheben an der Maschine
- Wadenheben mit Kurzhanteln
- Wadenheben mit Körpergewicht
- Wall Ball Shot
- Wall Sit
- Wall Walk
- Weites Bankdrücken an der Smith Machine
- Weites Bankdrücken mit Kurzhantel
- Weites Bankdrücken mit Langhantel
- Wide-Grip Push-up
- Windshield Wiper
- World's Greatest Hip Opener
- World's Greatest Stretch
- Y-T-W Raise am Kabelzug
- Y-T-W Raise mit Kurzhanteln
- Zercher-Kniebeuge mit Langhantel
- Überkopf-Trizepsstrecken mit Kurzhantel
- Überkopf-Trizepsstrecken mit Langhantel

# Spezielle Ausgaberegeln für Freeform-Text
- Bleibe immer im definierten Ausgabeformat. Keine zusätzlichen Strukturebenen. Ich habe eine weitere GenAI die Deinen Output in JSON überführt. Sie braucht exaktes Format!

# Ausgabeformat (keine Erklärungen, keine Aufzählungszeichen vor Blocknamen!)
```
Workout: <Name> (≈<Dauer> min | Fokus: <Schlagworte>)

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
Aktuelles Datum: 03.07.2025

User Prompt: 

Trainingsziele:
## Persönliche Informationen
Geschlecht: male
Alter: 31 Jahre
Körpergröße: 186.0 cm
Gewicht: 94.0 kg

## Trainingsziele
Bevorzugter Workout Style: Ausdauer-Wettkampftraining im Hyrox-Stil mit funktionalen Elementen
Beschreibung: Ich möchte deutlich stärker werden und meine Körperästhetik verbessern

## Erfahrungslevel
Fitnesslevel: Fit (4/7)
Trainingserfahrung: Erfahren (5/7)

## Trainingsplan
Trainingsfrequenz: 4x pro Woche
Trainingsdauer: 60 Minuten
Andere regelmäßige Aktivitäten: Joggen 2x pro Woche

## Equipment & Umgebung
Standard Ausrüstung: fitnessstudio
Zusätzliche Informationen: Zu Hause habe ich eine 24 kg Kettlebell, eine Klimmzug Stange und verschiedene Widerstands Bänder

## Einschränkungen
Verletzungen/Einschränkungen: Keine
Mobilitätseinschränkungen: Keine

## Zusätzliche Kommentare
Ich möchte nicht an der Rudermaschine arbeiten. Bitte mache für mich alle Cardio Übungen im Zirkel mit einem Ski Ergometer.

Trainingshistorie:
[{"name": "Hyrox-Style Kraft & Ausdauer Zirkel", "date": "2025-07-01", "blocks": [{"name": "Warm-Up", "exercises": [{"name": "Jumping Jacks", "sets": [{"duration": 60}]}, {"name": "Dynamic Walking Lunges", "sets": [{"reps": 10}]}, {"name": "Arm Circles", "sets": [{"reps": 10}]}]}, {"name": "Main Block - Kraft & Hyrox Hybrid", "exercises": [{"name": "Front Squat", "sets": [{"weight": 40.0, "reps": 8}, {"weight": 60.0, "reps": 6}, {"weight": 80.0, "reps": 5}, {"weight": 85.0, "reps": 5}]}, {"name": "Push Press", "sets": [{"weight": 30.0, "reps": 8}, {"weight": 40.0, "reps": 6}, {"weight": 50.0, "reps": 5}, {"weight": 55.0, "reps": 5}]}, {"name": "Ski Ergometer", "sets": [{"distance": 300.0, "count": 3}]}, {"name": "Sled Push", "sets": [{"distance": 20.0, "count": 3}]}, {"name": "Wall Ball Shot", "sets": [{"reps": 15, "count": 3}]}, {"name": "Burpee Broad Jump", "sets": [{"reps": 5, "count": 3}]}, {"name": "Plank Hold", "sets": [{"duration": 60, "count": 3}]}, {"name": "Russian Twist", "sets": [{"reps": 20, "count": 3}]}]}, {"name": "Cool-Down", "exercises": [{"name": "Hamstring Stretch (Seated Forward Fold)", "sets": [{"duration": 30}]}, {"name": "Couch Stretch", "sets": [{"duration": 30}]}, {"name": "Child's Pose", "sets": [{"duration": 60}]}]}], "focus": "Hyrox, Kraft, Ausdauer", "duration": 60}, {"name": "Hyrox-Style Kombination: Kraft & Ausdauer", "date": "2025-06-30", "blocks": [{"name": "Hauptteil - Kraftblock", "exercises": [{"name": "Back Squat", "sets": [{"weight": 100.0, "reps": 5, "count": 2}, {"weight": 20.0, "reps": 10}, {"weight": 60.0, "reps": 5}, {"weight": 100.0, "reps": 5}]}, {"name": "Kreuzheben", "sets": [{"weight": 60.0, "reps": 5}, {"weight": 90.0, "reps": 3}, {"weight": 120.0, "reps": 5, "count": 3}]}, {"name": "Bankdrücken", "sets": [{"weight": 40.0, "reps": 8}, {"weight": 50.0, "reps": 5}, {"weight": 70.0, "reps": 5, "count": 3}]}]}], "focus": "Hyrox, Kraft, Ausdauer", "duration": 60}]

# Output
Gib **nur** den Workout-Text in genau dem oben vorgegebenen Format zurück. 