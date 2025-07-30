# Muscle Fatigue Model - Phase 1 Dokumentation

## Überblick

Das Muscle Fatigue Model berechnet Recovery-Prozentsätze (0-100%) für 24 verschiedene Muskelgruppen basierend auf vergangenen Trainingseinheiten.

## Aktuelle Implementierung

### 1. Datenquellen
- **Training History**: Vergangene Workouts mit Sets und `completed_at` Zeitstempeln
- **Exercise Descriptions**: Muskelaktivierung pro Übung (z.B. Bankdrücken = 85% Chest, 60% Triceps)

### 2. Berechnung pro Set

Für jeden einzelnen Set wird die Ermüdung in mehreren Schritten berechnet:

```
Set-Ermüdung = Set-Volumen × Muskel-Aktivierung × Zeit-Decay × Recovery-Komplexitäts-Faktor
```

#### Set-Volumen Berechnung (abhängig von volume_unit)

**Reps Only** (Körpergewichtsübungen):
```
set_volume = reps × muscle_fatigue_factor
```

**Reps + Weight** (Gewichtsübungen):
```
set_volume = (reps × weight) × met_value / 100
```

**Time Based** (Isometrische Übungen):
```
set_volume = duration_seconds × met_value / 60
```

**Distance Based** (Lauftraining):
```
set_volume = distance × met_value
```

#### Fatigue-Faktoren Erklärt

**MET Value (Metabolic Equivalent):**
- Energieaufwand der Übung (4.0-8.0)
- Höhere Werte = intensivere Übungen
- Beispiele: Plank (4.0), Bench Press (6.5), Pull-ups (6.0)

**Muscle Fatigue Factor:**
- Spezifische Belastung für Muskulatur (0.8-1.6)
- Nur bei Körpergewichtsübungen verwendet
- Beispiele: Plank (1.0), Pull-ups (1.3), Bench Press (1.4)

**Recovery Complexity:**
- Wie schwer sich die Übung regeneriert
- **Low** (1.0): Face Pulls - schnelle Erholung
- **Medium** (1.2): Dips, Tricep Dips 
- **High** (1.4): Bench Press, Pull-ups - komplexe Bewegungen
- **Very High** (1.6): Deadlifts, Squats - systemische Belastung

#### Zeit-Decay Faktor
```
decay_factor = 0.7 ^ days_ago
```
- **1 Tag alt**: 0.7 (70% der ursprünglichen Ermüdung)
- **2 Tage alt**: 0.49 (49%)
- **3 Tage alt**: 0.343 (34%)

### 3. Recovery Percentage Berechnung

```
recovery_percentage = max(0, 100 - min(100, (fatigue_score / 1000) × 100))
```

**Aktueller Schwellwert**: `max_fatigue_threshold = 1000.0`

## Beispiel-Berechnung

### Bankdrücken Set: 100kg × 8 Reps (1 Tag alt)

**Schritt 1: Set-Volumen**
```
volume_unit = "reps_and_weight"
set_volume = (8 × 100) × 6.5 / 100 = 52.0
```

**Schritt 2: Faktoren**
- **Zeit-Decay**: `0.7^1 = 0.7` (1 Tag alt)
- **Recovery Complexity**: `1.4` (high)
- **Chest Aktivierung**: `85%` (0.85)

**Schritt 3: Ermüdung pro Muskelgruppe**
```
chest_fatigue = 52.0 × 0.85 × 0.7 × 1.4 = 43.3
triceps_fatigue = 52.0 × 0.60 × 0.7 × 1.4 = 30.6
shoulders_fatigue = 52.0 × 0.55 × 0.7 × 1.4 = 28.0
```

**Schritt 4: Recovery Percentage**
```
chest_recovery = 100 - min(100, (43.3 / 1000) × 100) = 95.7%
```

### Warum sind die Recovery-Werte so hoch?

**Problem**: Bei einem Schwellwert von 1000 führt selbst intensive Ermüdung zu hohen Recovery-Werten:
- Fatigue Score von 50 → Recovery = 95%
- Fatigue Score von 100 → Recovery = 90%
- Fatigue Score von 500 → Recovery = 50%

## Aktuelle Beispieldaten (29.07-27.07.2025)

### Workout 1 (29.07): Upper Body
- Archer Push-up: 3 Sets (8,6,5 Reps)
- Plank: 2 Sets (45s, 40s)
- Dead Hang: 2 Sets (30s, 25s)

### Workout 2 (28.07): Lower Body + Cardio
- Squats: 3 Sets (25,22,20 Reps)
- Running: 40min, 7km

### Workout 3 (27.07): Push Day
- Bench Press: 3 Sets (100kg×10, 100kg×8, 95kg×15)
- Archer Push-up: 2 Sets (8,6 Reps)

## Aktuelle Ergebnisse
- **Durchschnitt**: 100.0% Recovery
- **Niedrigste Werte**: Forearms (99.6%), Rectus Abdominis (99.8%), Latissimus (99.8%)

## Probleme & Verbesserungsbedarf

1. **Schwellwert zu hoch**: 1000 ist unrealistisch
2. **Zeit-Decay zu aggressiv**: 70% tägliche Erholung ist zu viel
3. **Volumen-Faktoren**: Möglicherweise zu niedrig skaliert
4. **Fehlende Kumulierung**: Mehrere Trainingseinheiten stapeln sich nicht ausreichend
5. **Keine Validierung**: Keine Benchmarks für "normale" vs "ermüdete" Muskeln

## Benchmark-Beispiel: Intensiver Push-Tag

### Beispiel-Workout (gestern absolviert)
```
🏋️ Intensiver Push-Tag - 5 Übungen, ~60min
1. Bankdrücken: 3×8 @ 100kg (Recovery: 2min)
2. Incline Dumbbell Press: 3×10 @ 35kg pro Hand (Recovery: 90s)
3. Dips: 3×12 @ Körpergewicht + 20kg (Recovery: 90s)
4. Overhead Press: 3×6 @ 70kg (Recovery: 2min)
5. Tricep Dips: 3×15 @ Körpergewicht (Recovery: 60s)
```

### Erwartete Recovery-Werte (24h später)
Nach einem solchen intensiven Push-Training sollten die Werte etwa so aussehen:

**Stark beanspruchte Muskeln:**
- **Chest**: 70-80% Recovery (Hauptzielmuskel, hohe Belastung)
- **Triceps**: 65-75% Recovery (Sekundär in allen Übungen stark involviert)
- **Shoulders Anterior**: 75-85% Recovery (Primär bei Overhead Press, sekundär bei anderen)

**Moderat beanspruchte Muskeln:**
- **Rectus Abdominis**: 85-90% Recovery (Stabilisation bei allen Übungen)

**Wenig/nicht beanspruchte Muskeln:**
- **Legs, Back, Biceps**: 95-100% Recovery (kaum beteiligt)

### Warum diese Werte realistisch sind
- Ein intensiver Push-Tag sollte die Zielmuskulatur deutlich ermüden
- 24h später ist noch keine vollständige Erholung erreicht
- Unterschiede zwischen primären und sekundären Muskeln sind erkennbar
- Nicht trainierte Muskelgruppen bleiben unbeeinträchtigt

## Aktuelles Problem
Mit dem jetzigen Modell würde selbst dieser intensive Workout zu ~98-100% Recovery führen, was unrealistisch ist.

## Nächste Schritte

1. **Schwellwert anpassen**: Von 1000 auf 50-200 reduzieren
2. **Zeit-Decay überdenken**: Langsamere Erholung (0.8-0.9 statt 0.7)
3. **Realitätscheck**: Benchmarks mit bekannten "müden" Szenarien erstellen
4. **Volumen-Kalibrierung**: Met-Values und Fatigue-Faktoren überprüfen
5. **Benchmark validieren**: Intensiven Push-Tag simulieren und Ergebnisse prüfen

## Vereinfachtes Satzbasiertes Modell - Phase 2 Ansatz

### Grundidee: Sätze pro Muskelgruppe zählen

Anstatt komplexer Volumen-/Ermüdungsberechnungen einfach **Sätze pro Muskelgruppe** über die letzten 7 Tage tracken:

```
muscle_weekly_sets = sum(sets_for_muscle_in_last_7_days)
recovery_percentage = max(0, 100 - (muscle_weekly_sets / target_weekly_sets) * 100)
```

### Warum das besser ist

**1. Einfachheit & Verständlichkeit**
- Jeder Fitnesstracker verwendet "Sätze pro Woche"
- Benutzer verstehen sofort: "3 von 12 Sätzen Chest diese Woche = 25% erreicht"
- Keine komplexen MET-Values oder Decay-Faktoren

**2. Direkte Ziel-Verfolgung**
- Zeigt sofort Fortschritt zum wöchentlichen Trainingsvolumen
- "Du hast noch 4 Chest-Sätze bis zu deinem Wochenziel"
- Motivierend und actionable

**3. Validierbar & Iterierbar**
- Einfach zu testen: "Nach 6 Chest-Sätzen sollte Chest bei 50% sein"
- Leicht anzupassen: Target-Sets pro Muskelgruppe verändern
- Weniger bewegliche Teile = weniger Fehlerquellen

### Implementierung - Satzbasiertes Modell

#### 1. Target Weekly Sets Definition
```python
# Beispiel-Targets (anpassbar pro User/Trainingslevel)
TARGET_WEEKLY_SETS = {
    'chest': 12,           # 3-4 Übungen x 3 Sets
    'triceps': 9,          # Sekundär in Push + direktes Training
    'shoulders_anterior': 8,
    'quadriceps': 15,      # Große Muskelgruppe
    'glutes': 12,
    'rectus_abdominis': 8,
    'latissimus': 10,
    # ... weitere Muskelgruppen
}
```

#### 2. Berechnung pro Muskelgruppe
```python
def calculate_set_based_recovery(muscle_group: str, last_7_days_workouts: List[Workout]) -> float:
    # Sätze für diese Muskelgruppe in den letzten 7 Tagen zählen
    total_sets = 0
    
    for workout in last_7_days_workouts:
        for exercise in workout.exercises:
            # Muskelaktivierung aus exercise_descriptions
            muscle_activation = get_muscle_activation(exercise.name, muscle_group)
            if muscle_activation > 0.3:  # Nur relevante Aktivierung zählen
                total_sets += len(exercise.sets)
    
    # Recovery = wie viel vom Wochenziel bereits erreicht
    target_sets = TARGET_WEEKLY_SETS.get(muscle_group, 10)
    completion_percentage = min(100, (total_sets / target_sets) * 100)
    
    # Recovery = 100% - completion_percentage
    # Bedeutung: 0% = frisch, 100% = Wochenziel erreicht
    return max(0, 100 - completion_percentage)
```

#### 3. Vorteile dieser Berechnung

**Intuitive Werte:**
- 100% Recovery = 0 Sätze diese Woche (frisch)
- 50% Recovery = 6/12 Chest-Sätze (halbes Wochenziel)
- 0% Recovery = 12/12 Chest-Sätze (Wochenziel erreicht)

**Direkte Actionability:**
- "Triceps: 33% Recovery → Noch 6 Sätze bis Wochenziel"
- "Chest: 0% Recovery → Wochenziel erreicht, andere Muskelgruppen fokussieren"

### 4. UI/UX Integration

#### Wöchentliche Ziel-Anzeige
```
🏋️ Wöchentliche Trainingsziele

✅ Chest: 12/12 Sätze (100% erreicht)
🔶 Triceps: 6/9 Sätze (67% erreicht)
⚪ Back: 2/10 Sätze (20% erreicht)
⚪ Legs: 0/15 Sätze (0% erreicht)
```

#### Workout-Recommendation Engine
```python
def recommend_muscle_groups_for_today(recovery_scores: Dict[str, float]) -> List[str]:
    # Empfehle Muskelgruppen mit höchster Recovery (wenig trainiert diese Woche)
    return sorted(recovery_scores.keys(), key=lambda m: recovery_scores[m], reverse=True)[:3]
```

### 5. Migration vom aktuellen Modell

**Phase 1**: Beide Modelle parallel laufen lassen
- Komplexes Modell für Analyse/Debugging
- Satzbasiertes Modell für User-facing Features

**Phase 2**: A/B Testing
- 50% User mit satzbasiertem Modell
- Engagement und Verständlichkeit messen

**Phase 3**: Vollständige Migration
- Satzbasiertes Modell als Standard
- Komplexes Modell für erweiterte Features (optional)

### 6. Erweiterungsmöglichkeiten

**Erweiterte Targets:**
- Beginner: 8-10 Sets/Woche pro Muskelgruppe
- Intermediate: 10-14 Sets/Woche
- Advanced: 14-20 Sets/Woche

**Zeitbasierte Anpassungen:**
- Aktuelle Woche: 100% Gewichtung
- Letzte Woche: 20% Gewichtung (für sanfte Übertragung)

**Intensitäts-Modifikator:**
- Schwere Sätze (1-5 Reps) = 1.5x Gewichtung
- Normale Sätze (6-12 Reps) = 1.0x Gewichtung
- Leichte Sätze (13+ Reps) = 0.8x Gewichtung

### 7. Warum das funktioniert

**Wissenschaftliche Basis:**
- Sätze pro Woche ist der wichtigste Hypertrophie-Faktor
- 10-20 Sets/Woche/Muskelgruppe ist optimal für die meisten Menschen
- Einfache Trackbarkeit führt zu besserer Adherence

**User Experience:**
- Sofort verständlich ohne Erklärung
- Klare Ziele und Fortschrittsanzeige
- Gamification-Potenzial (Wochenziele erreichen)

**Entwickler-Effizienz:**
- Weniger komplexe Logik = weniger Bugs
- Einfach zu testen und zu validieren
- Schnelle Iteration und Anpassungen möglich