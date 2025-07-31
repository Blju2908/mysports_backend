# Experiment: Minimal Output Token Optimization

## Hypothese
Die Workout-Generierung dauert hauptsächlich wegen der Token-Ausgabe so lange (36.09s). Durch drastische Reduzierung der Output-Tokens können wir die Geschwindigkeit signifikant erhöhen.

## Experiment-Design

### Phase 1: Baseline-Messung
- Aktuelle Ausgabe: ~250 Zeilen JSON mit detaillierten Sets
- Geschwindigkeit: 36.09s
- Token-Schätzung: ~2000-2500 Output-Tokens

### Phase 2: Minimal Output Test
- Neue Ausgabe: Nur Übungsnamen + Anzahl Sets
- Erwartete Geschwindigkeit: < 10s
- Token-Schätzung: ~200-300 Output-Tokens

## Implementierungsplan

### 1. Architektur für Prompt-Versionierung

```
backend/
├── app/
│   └── llm/
│       └── workout_generation/
│           ├── prompts/
│           │   ├── v1/                      # Aktueller Prompt
│           │   │   └── core_prompt.py
│           │   └── v2/                      # Minimal Output Prompt
│           │       └── core_prompt_minimal.py
│           ├── prompt_manager.py            # NEU: Prompt Version Manager
│           └── workout_generation_service.py
```

### 2. Prompt Manager Implementation

```python
# prompt_manager.py
from enum import Enum
from typing import Protocol

class PromptVersion(Enum):
    V1_FULL = "v1_full"
    V2_MINIMAL = "v2_minimal"

class WorkoutPromptProtocol(Protocol):
    def get_core_prompt(self) -> str:
        ...
    
    def get_output_format(self) -> str:
        ...

class PromptManager:
    def __init__(self, version: PromptVersion = PromptVersion.V1_FULL):
        self.version = version
        self._load_prompt()
    
    def _load_prompt(self):
        if self.version == PromptVersion.V1_FULL:
            from .prompts.v1.core_prompt import CorePromptV1
            self.prompt = CorePromptV1()
        elif self.version == PromptVersion.V2_MINIMAL:
            from .prompts.v2.core_prompt_minimal import CorePromptV2Minimal
            self.prompt = CorePromptV2Minimal()
```

### 3. Minimal Output Format

```python
# Statt des aktuellen detaillierten JSON Outputs:
{
  "blocks": [
    {
      "name": "Warm-Up",
      "exercises": [
        {"name": "Jumping Jacks", "sets": 1},
        {"name": "Arm Circles", "sets": 1}
      ]
    },
    {
      "name": "Main",
      "exercises": [
        {"name": "Pull-up", "sets": 3},
        {"name": "Kettlebell Goblet Squat", "sets": 3},
        {"name": "Push-up", "sets": 3},
        {"name": "Russian Kettlebell Swing", "sets": 3},
        {"name": "Plank Hold", "sets": 3}
      ]
    }
  ]
}
```

### 4. Post-Processing Pipeline

Nach der minimalen LLM-Ausgabe würde ein Post-Processor die Details ergänzen:

```python
class WorkoutPostProcessor:
    def __init__(self, user_history, equipment):
        self.user_history = user_history
        self.equipment = equipment
    
    def expand_minimal_workout(self, minimal_output):
        """
        Ergänzt die minimale Ausgabe mit:
        - Repetitions basierend auf Exercise-Typ und History
        - Weights basierend auf letzten Workouts
        - Rest periods basierend auf Exercise-Typ
        - Superset groups basierend auf Regeln
        """
        pass
```

### 5. Implementierungsschritte

#### Woche 1: Setup & Baseline
1. **Tag 1-2**: 
   - Prompt-Versionierungs-Architektur erstellen
   - PromptManager implementieren
   - Baseline-Messungen durchführen (10 Runs)

2. **Tag 3-4**:
   - V2 Minimal Prompt erstellen
   - Output-Format auf Minimal reduzieren
   - Integration in workout_generation_service.py

3. **Tag 5**:
   - Test-Script mit A/B Vergleich
   - Performance-Messungen

#### Woche 2: Post-Processing
1. **Tag 1-2**:
   - WorkoutPostProcessor Grundstruktur
   - Regel-basierte Parameter-Ergänzung

2. **Tag 3-4**:
   - Integration in Service
   - Validierung der generierten Workouts

3. **Tag 5**:
   - Performance-Optimierung
   - Dokumentation

### 6. Test-Script für Experiment

```python
# scripts/test_minimal_output.py
import asyncio
import time
from statistics import mean, stdev

async def run_comparison_test(n_runs=5):
    results = {
        "v1_full": [],
        "v2_minimal": []
    }
    
    for version in ["v1_full", "v2_minimal"]:
        for i in range(n_runs):
            start = time.time()
            # Run workout generation
            duration = time.time() - start
            results[version].append(duration)
    
    # Output comparison
    print(f"V1 Full: {mean(results['v1_full']):.2f}s ± {stdev(results['v1_full']):.2f}s")
    print(f"V2 Minimal: {mean(results['v2_minimal']):.2f}s ± {stdev(results['v2_minimal']):.2f}s")
    print(f"Speedup: {mean(results['v1_full']) / mean(results['v2_minimal']):.1f}x")
```

### 7. Erwartete Ergebnisse

#### Performance
- **V1 Full Output**: 36s (2500 tokens)
- **V2 Minimal Output**: 8-12s (300 tokens)
- **Speedup**: 3-4x

#### Token-Einsparung
- **Input Tokens**: Gleich bleibend
- **Output Tokens**: -88% Reduktion
- **Kosten**: -80% für Output

### 8. Risiken & Mitigationen

1. **Qualitätsverlust**
   - Mitigation: Robuster Post-Processor mit History-basierter Logik

2. **Edge Cases**
   - Mitigation: Fallback auf V1 wenn Post-Processing fehlschlägt

3. **Wartbarkeit**
   - Mitigation: Klare Trennung zwischen LLM-Output und Post-Processing

## Nächste Schritte

1. **Entscheidung**: Soll ich mit der Implementierung beginnen?
2. **Priorität**: Erst nur Minimal-Prompt oder gleich mit Post-Processor?
3. **Umgebung**: Development/Test-Setup bereit?

## Alternativer Ansatz: Streaming

Falls die Hypothesis falsch ist und nicht die Token-Ausgabe das Problem ist:
- Streaming-Response implementieren
- Erste Übungen sofort anzeigen
- Perceived Performance verbessern