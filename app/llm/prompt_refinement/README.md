# 🚀 S3ssions Prompt Refinement System

Ein sich selbst verbesserndes System für die Optimierung von Workout-Generierungs-Prompts mittels Multi-Agent LLM-Architektur.

## 🎯 Ziel

Das System automatisiert die Verbesserung der Workout-Generierung durch:
- **Kontinuierliche Analyse** der Prompt-Qualität
- **Intelligente Optimierung** basierend auf Fitness-Expertise
- **Validierung** durch A/B-Tests zwischen Workouts
- **Iterative Verbesserung** bis zum optimalen Prompt

## 🏗️ Architektur

### 3-Agent-System (Langchain-basiert)

1. **🔍 Critique Agent** (`CritiqueAgent`)
   - Analysiert generierte Workouts
   - Identifiziert Schwächen in Trainingslogik, Personalisierung, etc.
   - Bewertet Prompt-Compliance und App-Vision-Alignment
   - **Output**: Strukturierter Kritik-Report mit Verbesserungsvorschlägen

2. **⚡ Refine Agent** (`RefineAgent`)
   - Optimiert System-Prompts basierend auf Kritik
   - Implementiert Prompt Engineering Best Practices
   - Bewahrt kritische Elemente (Übungsbibliothek, Ausgabeformat)
   - **Output**: Verbesserter System-Prompt

3. **✅ Validate Agent** (`ValidateAgent`)
   - Vergleicht Original- vs. Verbessertes Workout
   - Objektive Bewertung basierend auf Fitness-Kriterien
   - Trifft finale Entscheidung über Prompt-Update
   - **Output**: Validierungsresultat mit Begründung

## 📁 Dateistruktur

```
backend/app/llm/prompt_refinement/
├── __init__.py              # Package initialization
├── agents.py                # 3 LLM-Agents (Langchain-basiert)
├── schemas.py               # Pydantic-Schemas für strukturierte Outputs
├── prompts.py               # Master-Prompts für alle Agents
├── refinement_system.py     # Hauptsystem mit Loop-Logik
├── run_refinement.py        # Ausführungs-Script
├── output/                  # Generierte Resultate und Backups
└── README.md               # Diese Dokumentation
```

## 🚀 Verwendung

### 1. Schnellstart

```bash
cd backend/app/llm/prompt_refinement
python run_refinement.py
```

### 2. Programmatische Verwendung

```python
from app.llm.prompt_refinement.refinement_system import run_prompt_refinement

results = await run_prompt_refinement(
    user_id="your-user-id",
    max_iterations=3,
    provider="openai",
    model_name="gpt-4o",
    use_production_db=False,
    save_iterations=True
)
```

### 3. Konfiguration

Bearbeite die Konfiguration in `run_refinement.py`:

```python
CONFIG = {
    "USER_ID": "your-user-id",           # User für Tests
    "MAX_ITERATIONS": 3,                 # Anzahl Verbesserungsiterationen
    "PROVIDER": "openai",                # LLM Provider
    "MODEL_NAME": "gpt-4o",             # Modell-Name
    "USE_PRODUCTION_DB": False,          # Produktions-DB verwenden
    "SAVE_ITERATIONS": True,             # Iterationen speichern
}
```

## 🔄 Refinement-Loop

### Ablauf pro Iteration:

1. **Workout-Generierung** mit aktuellem Prompt
2. **Kritik-Analyse** des generierten Workouts
3. **Prompt-Optimierung** basierend auf Kritik
4. **Neue Workout-Generierung** mit verbessertem Prompt
5. **A/B-Validierung** zwischen Original und Verbesserung
6. **Prompt-Update** nur bei nachgewiesener Verbesserung

### Stopp-Kriterien:

- **Maximale Iterationen** erreicht
- **Hohe Qualität** erreicht (Score ≥ 9/10)
- **Keine Verbesserung** in mehreren Iterationen

## 📊 Output & Tracking

### Automatische Speicherung:

- **Prompt-Backups**: `output/training_principles_iteration_X_TIMESTAMP.md`
- **Detaillierte Resultate**: `output/refinement_results_TIMESTAMP.json`
- **Aktuelle Prompts**: `../workout_generation/prompts/training_principles_base.md`

### Tracking-Metriken:

- **Critique Score**: 1-10 Bewertung der Workout-Qualität
- **Improvement Rate**: Prozentsatz erfolgreicher Verbesserungen
- **Weakness Categories**: Kategorisierung der identifizierten Schwächen
- **Validation Decisions**: A/B-Test-Resultate

## 🛠️ Technische Details

### Langchain-Integration

- **Multi-Provider Support**: OpenAI, Anthropic, Google
- **Structured Outputs**: Pydantic-Schemas für konsistente Resultate
- **Async Processing**: Vollständig asynchrone Verarbeitung
- **Error Handling**: Robuste Fehlerbehandlung mit Fallbacks

### Prompt Engineering

- **Value Proposition Integration**: S3ssions-Philosophie in allen Agents
- **Fitness-Expertise**: Trainingslogik und wissenschaftliche Prinzipien
- **Structured Reasoning**: Klare Bewertungskriterien und Formatierung
- **Iterative Refinement**: Kontinuierliche Verbesserung basierend auf Feedback

## 🎯 Bewertungskriterien

Das System bewertet Workouts nach:

1. **Trainingswissenschaft**: Wissenschaftliche Fundierung
2. **Personalisierung**: Anpassung an User-Profile und Historie
3. **Sicherheit**: Verletzungsprävention und angemessene Progression
4. **Effektivität**: Zielerreichung und Trainingsoptimierung
5. **S3ssions Value Prop**: "Ein Klick. Perfektes Workout."
6. **Prompt-Compliance**: Befolgung der System-Anweisungen
7. **App-Vision**: Alignment mit S3ssions-Philosophie

## 🔧 Erweiterungen

### Zusätzliche Agents:

- **Performance Agent**: Tracking von Workout-Performance-Metriken
- **User Feedback Agent**: Integration von User-Bewertungen
- **Trend Analysis Agent**: Analyse von Trainings-Trends

### Erweiterte Features:

- **Multi-User Testing**: Parallele Tests mit verschiedenen User-Profilen
- **Seasonal Optimization**: Anpassung an Jahreszeiten und Trends
- **Equipment-Specific Refinement**: Optimierung für spezifische Equipment-Setups

## 📈 Erwartete Verbesserungen

- **Höhere Workout-Qualität**: Bessere Trainingspläne durch kontinuierliche Optimierung
- **Personalisierung**: Präzisere Anpassung an individuelle Bedürfnisse
- **Effizienz**: Reduktion manueller Prompt-Optimierung
- **Konsistenz**: Gleichbleibend hohe Qualität über alle Workouts
- **Innovation**: Entdeckung neuer Trainingsansätze durch LLM-Creativity

## 🚨 Wichtige Hinweise

### Sicherheit:
- **Backup-System**: Automatische Backups vor Prompt-Updates
- **Rollback-Fähigkeit**: Einfache Wiederherstellung vorheriger Versionen
- **Validierung**: Keine Änderungen ohne nachgewiesene Verbesserung

### Performance:
- **Batch-Processing**: Effiziente Verarbeitung multipler Iterationen
- **Caching**: Wiederverwendung von User-Daten zwischen Iterationen
- **Parallelisierung**: Gleichzeitige Ausführung unabhängiger Agents

### Wartung:
- **Monitoring**: Kontinuierliche Überwachung der System-Performance
- **Logging**: Detaillierte Protokollierung aller Refinement-Schritte
- **Alerting**: Benachrichtigungen bei kritischen Fehlern

---

**Entwickelt für S3ssions - "Ein Klick. Perfektes Workout."** 