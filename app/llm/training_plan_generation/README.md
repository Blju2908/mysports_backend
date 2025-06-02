# Training Plan Regeneration Scripts

Dieses Verzeichnis enthält Skripte zur Regeneration von Trainingsplänen im neuen JSON-Format.

## Übersicht

Nach der Schema-Änderung müssen alle bestehenden Trainingspläne aktualisiert werden, um das neue `training_principles_json` Feld zu befüllen. Diese Skripte automatisieren diesen Prozess.

## Verfügbare Skripte

### 1. `regenerate_all_training_plans.py` (Hauptskript)

Das umfassende Skript mit verschiedenen Ausführungsmodi.

**Verwendung:**

```bash
# Alle Trainingspläne regenerieren
python regenerate_all_training_plans.py

# Dry Run (zeigt nur an, was verarbeitet würde)
python regenerate_all_training_plans.py --dry-run

# Bestimmte User-IDs regenerieren
python regenerate_all_training_plans.py --mode specific --users uuid1 uuid2 uuid3

# Mit angepasster Batch-Größe
python regenerate_all_training_plans.py --batch-size 5
```

**Parameter:**
- `--mode`: `all` (Standard) oder `specific`
- `--users`: Liste von User-IDs für spezifische Regeneration
- `--batch-size`: Anzahl User pro Batch (Standard: 10)
- `--dry-run`: Nur Vorschau, keine Änderungen

### 2. `batch_regenerate.py` (Einfaches Skript)

Vereinfachtes Skript ohne Command-Line-Argumente für schnelle Ausführung.

```bash
python batch_regenerate.py
```

### 3. `training_plan_generation_main.py` (Einzelner User)

Für das Testen mit einem einzelnen User.

```bash
python training_plan_generation_main.py
```

## Was passiert bei der Regeneration?

1. **Laden der Benutzerdaten**: Bestehende Trainingspla-Daten werden geladen
2. **LLM-Generierung**: Neue strukturierte Trainingsprinzipien werden mit der KI generiert
3. **JSON-Format**: Die Ergebnisse werden im neuen JSON-Schema gespeichert
4. **Rückwärtskompatibilität**: Markdown-Version wird für Legacy-Support erstellt
5. **Datenbank-Update**: Beide Formate werden in der Datenbank gespeichert

## Neues JSON-Schema

Das neue Schema enthält 5 strukturierte Bereiche:

```json
{
  "personal_information": { "content": "..." },
  "standard_equipment": { "content": "..." },
  "training_principles": { "content": "..." },
  "training_phases": { "content": "..." },
  "remarks": { "content": "..." },
  "valid_until": "2024-12-31"
}
```

## Sicherheitsfeatures

- **Batch-Verarbeitung**: Verhindert Überlastung der Datenbank
- **Error-Handling**: Einzelne Fehler stoppen nicht den gesamten Prozess
- **Logging**: Detaillierte Fehlerprotokolle in JSON-Format
- **Progress-Tracking**: Echtzeit-Fortschrittsanzeige
- **Dry-Run-Modus**: Sicheres Testen ohne Änderungen

## Error-Logs

Bei Fehlern wird automatisch eine `training_plan_regeneration_errors.json` erstellt:

```json
[
  {
    "user_id": "uuid-here",
    "error": "Error message",
    "timestamp": "2024-01-15T10:30:00"
  }
]
```

## Empfohlene Ausführung

1. **Test mit Dry-Run:**
   ```bash
   python regenerate_all_training_plans.py --dry-run
   ```

2. **Kleine Testgruppe:**
   ```bash
   python regenerate_all_training_plans.py --mode specific --users user-id-1 user-id-2
   ```

3. **Vollständige Regeneration:**
   ```bash
   python batch_regenerate.py
   ```

## Monitoring

- Überwache die Ausgabe auf Fehlerrate
- Prüfe Error-Logs bei Problemen
- Bei hoher Fehlerrate: Batch-Größe reduzieren
- LLM-Limits und Rate-Limiting beachten

## Troubleshooting

**Hohe Fehlerrate:**
- Batch-Größe reduzieren (`--batch-size 3`)
- LLM-Service-Verfügbarkeit prüfen
- Datenbankverbindung testen

**Einzelne User-Fehler:**
- User-Daten auf Vollständigkeit prüfen
- Spezifische Regeneration mit `--mode specific`

**Timeout-Probleme:**
- Kleinere Batch-Größe verwenden
- Pause zwischen Batches erhöhen (im Code anpassbar)

## Entwicklung

Beim Hinzufügen neuer Features:
- Error-Handling beibehalten
- Progress-Tracking aktualisieren
- Tests mit Dry-Run-Modus durchführen
- Dokumentation erweitern 