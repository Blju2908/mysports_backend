# Workout Rationale Generator

Dieses Modul generiert sportwissenschaftliche Begründungen für Workouts, die für TikTok-Content verwendet werden können.

## Funktionsweise

Das System lädt basierend auf der **User-ID** den Trainingsplan und die Trainingshistorie, sowie ein spezifisches Workout über die **Workout-ID**. Daraus wird eine sportwissenschaftliche Begründung generiert, die erklärt warum genau dieses Training durchgeführt wird.

## Verwendung

### Via Command Line

```bash
# Mit User-ID und Workout-ID als Parameter (lokale DB)
python backend/app/llm/workout_rationale/workout_rationale_main.py <user-id> <workout-id>

# Direkt mit Produktionsdatenbank
python backend/app/llm/workout_rationale/workout_rationale_main.py --prod <user-id> <workout-id>
python backend/app/llm/workout_rationale/workout_rationale_main.py --production

# Interaktive Eingabe (mit Datenbankwahl)
python backend/app/llm/workout_rationale/workout_rationale_main.py
```

### Programmatisch

```python
from app.llm.workout_rationale.workout_rationale_service import generate_workout_rationale
from uuid import UUID

# Generiere Rationale für Workout (lokale DB)
rationale = await generate_workout_rationale(
    user_id=UUID("user-uuid"), 
    workout_id=123
)

# Mit Produktionsdatenbank
rationale = await generate_workout_rationale(
    user_id=UUID("user-uuid"), 
    workout_id=123, 
    use_production_db=True
)
print(rationale)
```

## Input-Parameter

- **User-ID (UUID)**: Identifiziert den Benutzer für Trainingshistorie und Trainingsplan
- **Workout-ID (int)**: Identifiziert das spezifische Workout, das analysiert werden soll
- **Datenbankwahl**: Lokal oder Produktionsdatenbank

## Output

Das System generiert eine Textdatei mit folgendem Namen:
```
workout_rationale_user_{user_id}_workout_{workout_id}_{timestamp}.txt
```

Die Begründung ist optimiert für:
- **TikTok-Content**: 150-250 Wörter
- **Verständlichkeit**: Wissenschaftlich fundiert aber für Laien verständlich
- **Engagement**: Mit Hook, Hauptteil und motivierendem Ausblick

## Datenquellen

Das System kombiniert folgende Informationen:

1. **Aktuelles Workout**: Details, Übungen, Sets, Status
2. **Trainingsplan**: Ziele, Erfahrungslevel, Equipment, Einschränkungen
3. **Trainingshistorie**: Letzte 10 absolvierte Workouts für Kontext
4. **Sportwissenschaftlicher Kontext**: Periodisierung, Progression, Adaptationen

## Struktur

- `workout_rationale_main.py` - Hauptskript für CLI-Verwendung
- `workout_rationale_service.py` - Business Logic und DB-Zugriffe
- `workout_rationale_chain.py` - LLM-Interaktion
- `workout_rationale_prompt.md` - Prompt-Template
- `output/` - Ausgabe-Verzeichnis für generierte Dateien

## Abhängigkeiten

- Zugriff auf die Datenbank (Workout, TrainingPlan, User)
- OpenAI API Key in der Konfiguration
- Trainingshistorie und Trainingsplan des Users

## Ähnlichkeit zur Workout Generation

Das System folgt dem gleichen Pattern wie `workout_generation`:
- Explizite User-ID für Trainingskontext
- Strukturierte Datenaufbereitung
- Wiederverwendbare Service-Funktionen
- Saubere Trennung von DB-Logic und LLM-Logic 