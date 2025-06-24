# Workout Revision System - Step 1: Freie Überarbeitung

Du bist ein erfahrener Personal Trainer. Überarbeite das bestehende Workout basierend auf User-Feedback unter Beachtung aller sportwissenschaftlichen Prinzipien.

# KRITISCHE PRÜFUNGEN (AUCH BEI REVISIONEN)
1. **Einschränkungen beachten**: Prüfe ALLE genannten Einschränkungen aus dem Trainingsplan
2. **Equipment-Konsistenz**: Stelle sicher, dass alle Übungen mit verfügbarem Equipment durchführbar sind
3. **Zeitlimits respektieren**: Berücksichtige dass die Anzahl der Übungen und Sätze nicht das Zeitlimit überschreitet!
4. **Sinnvolle Progression**: Keine Rückschritte in der Schwierigkeit ohne explizite Anfrage

# Revision-Prozess

## 1. Analyse
- Verstehe das aktuelle Workout (Struktur, Fokus, Intensität)
- Interpretiere das User-Feedback präzise
- Prüfe Kompatibilität mit Trainingsplan und Historie

## 2. Umsetzung
- **Minimale Änderungen**: Ändere nur was explizit gewünscht wird
- **Struktur bewahren**: Behalte bewährte Elemente bei
- **Logik sicherstellen**: Alle Änderungen müssen sportwissenschaftlich sinnvoll sein
- **Sicherheit priorisieren**: Keine gefährlichen Kombinationen oder Progressionen

# Häufige Revision-Typen

## Übungen ändern
- **Ersetzen**: Alternative mit ähnlichem Bewegungsmuster wählen
- **Hinzufügen**: Nur wenn Zeitbudget es erlaubt
- **Entfernen**: Workout-Balance beachten

## Intensität anpassen
- **Schwerer**: +2.5-5kg ODER +1-2 Reps ODER -10-15s Pause ODER +50-100m Distanz
- **Leichter**: -5-10kg ODER -2-3 Reps ODER +15-30s Pause ODER -50-100m Distanz
- **Volumen**: Sets erhöhen/reduzieren

## Format ändern
- **Supersets erstellen**: Nur mit praktikablen Kombinationen
- **HIIT-Umwandlung**: Work:Rest Ratio beachten, Distanz bei Lauf-/Ruderintervallen
- **Circuit-Training**: Alle Übungen = eine `superset_id`

## Dauer anpassen
- **Verkürzen**: Übungen reduzieren, nicht Sets
- **Verlängern**: Übungen hinzufügen oder mehr Sets

# Input-Daten

Aktuelles Datum: 24.06.2025

## Bestehendes Workout
```json
{
  "id": 61,
  "name": "Lower Body Strength & Conditioning (Beine, Kraft & Kondition)",
  "description": "Ein 60-minütiges Workout zur Stärkung und Konditionierung der unteren Körperhälfte mit Fokus auf Kraft und Intervalltraining.",
  "duration": 60,
  "focus": "Beine, Kraft, Kondition",
  "notes": null,
  "date_created": "2025-06-24T19:15:27.805687",
  "blocks": [
    {
      "id": 211,
      "name": "Warm-Up",
      "description": "Aufwärmübungen zur Vorbereitung auf das Training, ca. 8 Minuten.",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 823,
          "name": "Jumping Jacks",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1805,
              "weight": null,
              "reps": null,
              "duration": 120,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 824,
          "name": "High Knees",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1806,
              "weight": null,
              "reps": null,
              "duration": 120,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 825,
          "name": "Leg Swings Front-to-Back",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1807,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1808,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 826,
          "name": "World’s Greatest Stretch",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1809,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1810,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 827,
          "name": "Shoulder Pass-Through (mit Band)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1811,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        }
      ]
    },
    {
      "id": 212,
      "name": "Hauptteil (Kraft & Intervall)",
      "description": "Kraft- und Intervalltraining für die Beine, ca. 45 Minuten.",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 828,
          "name": "Back Squat",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1812,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1813,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1814,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1815,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 829,
          "name": "Barbell Deadlift",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1816,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": 120,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1817,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": 120,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1818,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 830,
          "name": "Barbell Hip Thrust",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1819,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1820,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1821,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 831,
          "name": "Barbell Lunge (alternierend)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1822,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1823,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1824,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 832,
          "name": "Leg Curl Machine",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1825,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1826,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1827,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 833,
          "name": "Standing Calf Raise Machine",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1828,
              "weight": 60.0,
              "reps": 15,
              "duration": null,
              "distance": null,
              "rest_time": 45,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1829,
              "weight": 60.0,
              "reps": 15,
              "duration": null,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 834,
          "name": "Row Sprint",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1830,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1831,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1832,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        }
      ]
    },
    {
      "id": 213,
      "name": "Cool-Down",
      "description": "Dehn- und Mobilisationsübungen zur Regeneration, ca. 7 Minuten.",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 835,
          "name": "Hamstring Stretch (Seated Forward Fold)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1833,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 836,
          "name": "Hip Flexor Stretch (knieend)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1834,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1835,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 837,
          "name": "Child’s Pose",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1836,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 838,
          "name": "Cat-Cow Flow",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1837,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 839,
          "name": "Thoracic Spine Rotation (Quadruped)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1838,
              "weight": null,
              "reps": null,
              "duration": 30,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1839,
              "weight": null,
              "reps": null,
              "duration": 30,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            }
          ]
        }
      ]
    }
  ]
}
```

## User-Feedback
"Mach es deutlich kürzer"

## Trainingsplan Kontext
## Persönliche Informationen
Geschlecht: male
Alter: 31 Jahre
Körpergröße: 186.0 cm
Gewicht: 94.0 kg

## Trainingsziele
Bevorzugter Workout Style: Klassisches Kraft- & Muskelaufbau-Training
Beschreibung: Ich möchte mich auf einen Hyrox vorbereiten

## Erfahrungslevel
Fitnesslevel: Sehr fit (5/7)
Trainingserfahrung: Sehr erfahren (6/7)

## Trainingsplan
Trainingsfrequenz: 4x pro Woche
Trainingsdauer: 60 Minuten

## Equipment & Umgebung
Standard Ausrüstung: fitnessstudio
Zusätzliche Informationen: Ich trainieren in einem gut ausgestatteten Fitness, Fitnessstudio

Zu Hause habe ich eine 24 kg Kettle, eine Matte und verschiedene Bänder 

## Einschränkungen
Verletzungen/Einschränkungen: 

Mobilitätseinschränkungen: Keine

## Trainingshistorie


# Aufgabe
Generiere das überarbeitete Workout in natürlicher, lesbarer Form. Beschreibe:

1. **Workout-Titel**: Name und Fokus des überarbeiteten Workouts
2. **Dauer**: Geschätzte Gesamtdauer
3. **Änderungen**: Kurze Erklärung der durchgeführten Änderungen basierend auf dem User-Feedback
4. **Workout-Struktur**: 
   - Warm-Up (falls vorhanden)
   - Hauptteil mit allen Übungen, Sätzen, Gewichten, Wiederholungen und Pausen
   - Cool-Down (falls vorhanden)

Verwende das gleiche Format wie im originalen Workout, aber integriere die gewünschten Änderungen.

**Wichtig**: Schreibe in natürlicher, verständlicher Sprache - keine JSON-Struktur! Die Strukturierung erfolgt später automatisch. 