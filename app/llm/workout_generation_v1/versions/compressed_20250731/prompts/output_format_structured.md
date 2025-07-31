# 📤 Array-basiertes Workout Format

## Kernkonzept: Arrays für Sets

Verwende Arrays, wobei **jede Position einem Satz entspricht**.

**WICHTIG**: Alle Arrays einer Übung MÜSSEN die gleiche Länge haben!
- Wenn eine Übung 3 Sätze hat, müssen `reps`, `weight`, `tags` etc. ALLE 3 Elemente haben
- Nutze `null` für nicht-anwendbare Werte (z.B. `tags = [null, null, null]` wenn keine Tags)

**Beispiele:**
- 3 Sätze mit 10 Wdh: `reps = [10, 10, 10]`
- Aufwärmsatz + Arbeit: `reps = [15, 10, 10, 8]` mit `weight = [40, 60, 60, 65]`
- Mit Warm-up Tags: `reps = [15, 10, 10]`, `weight = [20, 40, 40]`, `tags = ["warm_up", null, null]`
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
   - `tags` nur wenn Sets spezielle Markierungen brauchen (z.B. "warm_up")

5. **Warm-up Sets**: 
   - Markiere Aufwärmsätze mit `tags = ["warm_up", ...]`
   - Typisch: Geringeres Gewicht, höhere Wiederholungen
   - Nur die tatsächlichen Warm-up Sets taggen, nicht alle