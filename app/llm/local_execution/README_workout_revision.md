# Workout Revision System

Dieses System ermöglicht es, bestehende Workouts basierend auf User-Feedback zu überarbeiten und zu verbessern.

## Komponenten

### 1. Chain (`workout_revision_chain.py`)
- **Funktion**: `revise_workout()`
- **Zweck**: Hauptlogik für die LLM-basierte Workout-Überarbeitung
- **Input**: Bestehendes Workout (als Dict), User-Feedback, optionaler Kontext
- **Output**: Überarbeitetes Workout als `WorkoutSchema`

### 2. Service (`workout_revision_service.py`)
- **Funktion**: `run_workout_revision_chain()`
- **Zweck**: Orchestriert den Revision-Prozess
- **Funktionen**:
  - Lädt bestehendes Workout aus der Datenbank
  - Konvertiert Workout-Objekte in LLM-kompatible Dictionaries
  - Führt die Revision Chain aus

### 3. Schemas (`workout_revision_schemas.py`)
- **WorkoutRevisionRequestSchema**: Für API-Anfragen
- **WorkoutRevisionResponseSchema**: Für API-Antworten
- **WorkoutRevisionPreviewSchema**: Für Vorschau-Funktionalität
- **WorkoutRevisionConfirmationSchema**: Für Bestätigungsprozess

### 4. Prompt (`workout_revision_prompt.md`)
- Detaillierte Anweisungen für das LLM
- Strukturierte Formatierung für verschiedene Änderungstypen
- Sicherheits- und Qualitätsrichtlinien

## Lokale Ausführung

### Test der Imports
```bash
cd backend
python app/llm/local_execution/test_revision_imports.py
```

### Workout-Revision testen
```bash
cd backend
python app/llm/local_execution/revise_workout_main.py
```

## Konfiguration für lokale Tests

In `revise_workout_main.py` können Sie folgende Parameter anpassen:

```python
# ID des zu überarbeitenden Workouts
workout_id = 1

# User-Feedback
user_feedback = "Bitte ersetze das Bankdrücken durch Liegestütze"

# Optionaler Kontext
training_plan = ""  # Trainingsplan als String
training_history = ""  # Trainingshistorie als JSON-String
```

## Typische Anwendungsfälle

1. **Übungen ersetzen**: "Ersetze Bankdrücken durch Kurzhantel-Bankdrücken"
2. **Intensität anpassen**: "Mache es schwerer/leichter"
3. **Dauer ändern**: "Verkürze das Workout auf 30 Minuten"
4. **Fokus verschieben**: "Mehr Fokus auf Cardio"
5. **Sets/Reps anpassen**: "Weniger Wiederholungen, mehr Gewicht"
6. **Übungen hinzufügen**: "Füge Bauchübungen hinzu"
7. **Übungen entfernen**: "Keine Beinübungen heute"

## Output

Das System erstellt JSON-Dateien mit:
- Original Workout ID (Referenz)
- User Feedback
- Überarbeitetes Workout
- Timestamp der Revision

Beispiel: `revised_workout_output_20241201_143022.json`

## Nächste Schritte

1. **API Endpoints**: Integration in FastAPI-Router
2. **Confirmation Flow**: UI für Bestätigung vor Speicherung
3. **Versioning**: Workout-Versionen verwalten
4. **History**: Revision-Historie verfolgen

## Abhängigkeiten

- LangChain
- OpenAI API
- SQLModel/SQLAlchemy
- Pydantic
- Bestehende Workout-Services 