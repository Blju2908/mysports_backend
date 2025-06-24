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
  "name": "Lower Body Strength & Conditioning",
  "description": "Workout: Lower Body Strength & Conditioning (≈60 min | Fokus: Beine, Kraft, Kondition)",
  "duration": 60,
  "focus": "Beine, Kraft, Kondition",
  "notes": null,
  "date_created": "2025-06-24T19:15:27.805687",
  "blocks": [
    {
      "id": 204,
      "name": "Warm-Up",
      "description": "Ganzkörpermobilisation & Aktivierung",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 789,
          "name": "Jumping Jacks",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1736,
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
          "id": 790,
          "name": "High Knees",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1737,
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
          "id": 791,
          "name": "Leg Swings Front-to-Back",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1738,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1739,
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
          "id": 792,
          "name": "World’s Greatest Stretch",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1740,
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
          "id": 793,
          "name": "Shoulder Pass-Through",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1741,
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
      "id": 205,
      "name": "Main",
      "description": "Kraft & Intervall",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 794,
          "name": "Back Squat",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1742,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1743,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1744,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1745,
              "weight": 100.0,
              "reps": 5,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 795,
          "name": "Trap Bar Deadlift",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1746,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": 120,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1747,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": 120,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1748,
              "weight": 110.0,
              "reps": 6,
              "duration": null,
              "distance": null,
              "rest_time": 120,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 796,
          "name": "Barbell Hip Thrust",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1749,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1750,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1751,
              "weight": 80.0,
              "reps": 10,
              "duration": null,
              "distance": null,
              "rest_time": 90,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 797,
          "name": "Barbell Lunge",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1752,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1753,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1754,
              "weight": 50.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 798,
          "name": "Leg Curl Machine",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1755,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1756,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1757,
              "weight": 45.0,
              "reps": 12,
              "duration": null,
              "distance": null,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 799,
          "name": "Standing Calf Raise Machine",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1758,
              "weight": 60.0,
              "reps": 15,
              "duration": null,
              "distance": null,
              "rest_time": 45,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1759,
              "weight": 60.0,
              "reps": 15,
              "duration": null,
              "distance": null,
              "rest_time": 45,
              "status": "open",
              "completed_at": null
            }
          ]
        },
        {
          "id": 800,
          "name": "Row Sprint 250 m",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1760,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1761,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1762,
              "weight": null,
              "reps": null,
              "duration": null,
              "distance": 250.0,
              "rest_time": 60,
              "status": "open",
              "completed_at": null
            }
          ]
        }
      ]
    },
    {
      "id": 206,
      "name": "Cool-Down",
      "description": "Dehnung & Mobilität",
      "notes": null,
      "is_amrap": false,
      "amrap_duration_minutes": null,
      "exercises": [
        {
          "id": 801,
          "name": "Hamstring Stretch (Seated Forward Fold)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1763,
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
          "id": 802,
          "name": "Hip Flexor Stretch (Kneeling)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1764,
              "weight": null,
              "reps": null,
              "duration": 60,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1765,
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
          "id": 803,
          "name": "Child’s Pose",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1766,
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
          "id": 804,
          "name": "Cat-Cow Flow",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1767,
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
          "id": 805,
          "name": "Thoracic Spine Rotation (Quadruped)",
          "description": null,
          "notes": null,
          "superset_id": null,
          "sets": [
            {
              "id": 1768,
              "weight": null,
              "reps": null,
              "duration": 30,
              "distance": null,
              "rest_time": null,
              "status": "open",
              "completed_at": null
            },
            {
              "id": 1769,
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
"Ich habe keine Trap Bar"

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