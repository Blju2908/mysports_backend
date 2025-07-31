# 📤 Array-basiertes Workout Format

## Kernkonzept: Arrays für Sets

Verwende Arrays, wobei **jede Position einem Satz entspricht**:

**Beispiele:**
- 3 Sätze mit 10 Wdh: `reps = [10, 10, 10]`
- Aufwärmsatz + Arbeit: `reps = [15, 10, 10, 8]` mit `weight = [40, 60, 60, 65]`
- Zeitbasiert: `duration = [60, 60, 45]` für Plank
- Einheitliche Pause: `rest = 90` (einzelner Wert)
- Variable Pausen: `rest = [60, 90, 90, 120]` (Array)

## Kritische Regeln

1. **Equipment-Beschränkungen**: Verwende NUR verfügbare Gewichte
   - Wenn User nur 24kg KB hat → alle KB-Übungen mit 24kg

2. **Unilaterale Übungen**: IMMER mit superset-Attribut
   - Erstelle "(rechts)" und "(links)" Varianten
   - Gib beiden das gleiche superset-Attribut (z.B. "A")

3. **Sprache**: 
   - Beschreibungen: Deutsch
   - Übungsnamen: Englisch (exakt aus Bibliothek)

4. **Felder weglassen wenn nicht anwendbar**:
   - Kein `weight` bei Bodyweight
   - Kein `duration` bei Wiederholungen
   - Kein `distance` außer bei Carries/Läufen