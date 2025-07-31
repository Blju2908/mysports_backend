# Workout Visualization

Dieses Tool ermöglicht es, die generierten Workout-JSON-Dateien aus dem `output`-Ordner in einer benutzerfreundlichen HTML-Oberfläche zu visualisieren.

## Verwendung

1. **HTML-Datei öffnen**: Öffne `workout_viewer.html` in deinem Browser
2. **JSON-Dateien laden**: Klicke auf "📁 JSON-Dateien auswählen" und wähle eine oder mehrere JSON-Dateien aus dem `../workout_generation/output/` Ordner aus
3. **Workouts betrachten**: Die Workouts werden automatisch geladen und übersichtlich dargestellt

## Features

### 🎯 Workout-Übersicht
- **Name & Beschreibung**: Klar strukturierte Darstellung des Workout-Namens und der Beschreibung
- **Meta-Informationen**: Dauer, Fokus und Dateiname werden prominent angezeigt
- **Chronologische Sortierung**: Neueste Workouts werden zuerst angezeigt

### 🏗️ Block-Struktur
- **Warm-Up, Hauptteil, Cool-Down**: Jeder Block wird separat dargestellt
- **Farbkodierung**: Verschiedene Blöcke haben unterschiedliche visuelle Kennzeichnungen
- **Block-Beschreibungen**: Zusätzliche Informationen zu jedem Block

### 💪 Übungs-Details
- **Übungsname**: Klar lesbare Darstellung der Übungsnamen
- **Superset-Kennzeichnung**: Supersets werden visuell hervorgehoben
- **Set-Informationen**: Detaillierte Anzeige von Gewicht, Wiederholungen, Zeit, Distanz und Pausen

### 📊 Set-Darstellung
- **Strukturierte Anzeige**: Jeder Set wird mit allen relevanten Werten angezeigt
- **Einheiten**: Automatische Zuordnung von Einheiten (kg, Wiederholungen, Sekunden, etc.)
- **Nummerierung**: Sets sind durchnummeriert für bessere Übersicht

### 🎨 Design-Features
- **Responsive Design**: Funktioniert auf Desktop und Mobile
- **Moderne UI**: Sauberes, professionelles Design
- **Hover-Effekte**: Interaktive Elemente für bessere Benutzererfahrung
- **Fehlerbehandlung**: Klare Fehlermeldungen bei Problemen

## Technische Details

### Datenstruktur
Die HTML-Seite erwartet JSON-Dateien mit folgender Struktur:
```json
{
  "name": "Workout Name",
  "description": "Workout Beschreibung",
  "duration": 45,
  "focus": "Kraft, Ausdauer",
  "blocks": [
    {
      "name": "Block Name",
      "description": "Block Beschreibung",
      "exercises": [
        {
          "name": "Übungsname",
          "superset_id": "A", // optional
          "sets": [
            {
              "values": [100, 8, null, null, 60], // [Gewicht, Reps, Zeit, Distanz, Pause]
              "position": 0
            }
          ]
        }
      ]
    }
  ]
}
```

### Values Array
Das `values` Array in jedem Set enthält:
- Index 0: Gewicht (kg)
- Index 1: Wiederholungen
- Index 2: Zeit (Sekunden)
- Index 3: Distanz (Meter)
- Index 4: Pause (Sekunden)

`null` Werte werden nicht angezeigt.

## Verwendung für Qualitätsbewertung

Diese Visualisierung hilft dabei, schnell die Qualität der generierten Workouts zu bewerten:

1. **Struktur-Check**: Sind alle Blöcke (Warm-Up, Hauptteil, Cool-Down) vorhanden?
2. **Übungsauswahl**: Sind die Übungen sinnvoll und abwechslungsreich?
3. **Progressions-Check**: Steigern sich Gewichte/Wiederholungen sinnvoll?
4. **Superset-Logik**: Werden Supersets korrekt gruppiert?
5. **Timing**: Sind Pausen und Gesamtdauer realistisch?

## Erweiterungen

Die HTML-Datei kann einfach erweitert werden um:
- Vergleichsfunktionen zwischen Workouts
- Export-Funktionen
- Filtermöglichkeiten
- Statistiken und Analysen 