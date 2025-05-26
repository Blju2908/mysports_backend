# LLM Call Logging System

## Überblick

Das LLM Call Logging System dokumentiert alle LLM-bezogenen API-Aufrufe in der Anwendung. Es ermöglicht:

- **Monitoring**: Überwachung der LLM-Nutzung und Performance
- **Debugging**: Detaillierte Fehlerinformationen bei LLM-Aufrufen
- **Analytics**: Statistiken über Nutzungsverhalten und Erfolgsraten
- **Security**: Nachverfolgung von API-Zugriffen pro User

## Model: LlmCallLog

Das `LlmCallLog` Model speichert folgende Informationen:

```python
class LlmCallLog(SQLModel, table=True):
    id: int                              # Primary Key
    user_id: str                         # UUID des Users
    endpoint_name: str                   # Name des Endpoints (z.B. "llm/create-workout")
    method: str                          # HTTP Method (POST, GET, etc.)
    timestamp: datetime                  # Zeitstempel des Aufrufs
    duration_ms: Optional[int]           # Dauer in Millisekunden
    success: bool                        # Erfolg/Fehler Status
    http_status_code: Optional[int]      # HTTP Status Code
    error_message: Optional[str]         # Fehlernachricht
    error_type: Optional[str]           # Fehlertyp (HTTPException, etc.)
    request_data: Optional[dict]         # Request-Daten (optional)
    response_summary: Optional[str]      # Zusammenfassung der Response
    llm_operation_type: Optional[str]    # Art der LLM-Operation
    workout_id: Optional[int]           # Workout ID (falls relevant)
    training_plan_id: Optional[int]     # Training Plan ID (falls relevant)
    user_agent: Optional[str]           # User Agent
    ip_address: Optional[str]           # IP-Adresse
```

## Implementierte Endpoints

### 1. LLM Endpoint (`/llm/create-workout`)
- **Operation Type**: `workout_creation`
- **Loggt**: User-Prompt, Workout-ID der erstellten Workouts
- **Context Manager**: `log_workout_creation()`

### 2. LLM Endpoint (`/llm/create-training-principles`)
- **Operation Type**: `training_principles_creation`
- **Loggt**: Training Plan Daten (ohne sensible Informationen)
- **Context Manager**: `log_training_principles_creation()`

### 3. Workout Revision (`/workouts/{workout_id}/revise`)
- **Operation Type**: `workout_revision`
- **Loggt**: User Feedback, Workout ID
- **Context Manager**: `log_workout_revision()`

### 4. Workout Revision Accept (`/workouts/{workout_id}/revise/accept`)
- **Operation Type**: `workout_revision_accept`
- **Loggt**: Revised Workout Details
- **Context Manager**: `log_workout_revision_accept()`

## Usage

### Automatisches Logging mit Context Manager

```python
from app.services.llm_logging_service import log_workout_creation

async with log_workout_creation(
    db=db, 
    user=current_user, 
    request=request,
    request_data={"prompt": user_prompt}
) as call_logger:
    try:
        # Your LLM operation here
        result = await some_llm_operation()
        
        # Log success
        await call_logger.log_success(
            http_status_code=200,
            response_summary="Operation completed successfully"
        )
        
        return result
    except Exception as e:
        # Error wird automatisch geloggt
        raise
```

### Manuelles Logging

```python
from app.services.llm_logging_service import LlmCallLogger

logger = LlmCallLogger(
    db=db,
    user=current_user,
    endpoint_name="custom/endpoint",
    llm_operation_type="custom_operation"
)

await logger.start_logging({"custom": "data"})

try:
    # Your operation
    result = await operation()
    await logger.log_success(response_summary="Success")
except Exception as e:
    await logger.log_error(e)
```

## Log-Anzeige Endpoints

### GET `/llm-logs/my-logs`
Zeigt die eigenen LLM-Logs des authentifizierten Users an.

**Query Parameters:**
- `endpoint_name`: Filter nach Endpoint
- `llm_operation_type`: Filter nach Operation Type
- `success`: Filter nach Erfolg (true/false)
- `days`: Anzahl Tage rückblickend (default: 7)
- `limit`: Max. Anzahl Ergebnisse (default: 50)

### GET `/llm-logs/my-summary`
Zeigt Statistiken der eigenen LLM-Nutzung an.

**Query Parameters:**
- `days`: Anzahl Tage für die Statistik (default: 7)

**Response:**
```json
{
  "total_calls": 42,
  "successful_calls": 40,
  "failed_calls": 2,
  "success_rate": 95.24,
  "average_duration_ms": 1234.5,
  "most_used_endpoints": {
    "llm/create-workout": 25,
    "workout/revise": 10
  },
  "operation_types": {
    "workout_creation": 25,
    "workout_revision": 10
  },
  "error_types": {
    "HTTPException": 2
  },
  "date_range": "2025-05-19 to 2025-05-26"
}
```

### GET `/llm-logs/` (Admin)
Zeigt alle LLM-Logs mit erweiterten Filteroptionen (für Admins).

**Query Parameters:**
- `user_id`: Filter nach User ID
- `endpoint_name`: Filter nach Endpoint
- `llm_operation_type`: Filter nach Operation Type
- `success`: Filter nach Erfolg
- `start_date`: Von-Datum
- `end_date`: Bis-Datum
- `limit`: Max. Anzahl Ergebnisse
- `offset`: Pagination Offset

## Security

- **User Isolation**: Users können nur ihre eigenen Logs einsehen
- **Sensitive Data**: Request-Daten werden nur bei Bedarf geloggt
- **Admin Access**: Vollzugriff auf alle Logs (TODO: Admin-Rollen implementieren)

## Performance Considerations

- **Async Operations**: Alle DB-Operationen sind asynchron
- **Error Handling**: Logging-Fehler beeinträchtigen nicht die Hauptoperation
- **Indexes**: Empfohlene DB-Indexes für bessere Performance:
  ```sql
  CREATE INDEX idx_llm_logs_user_timestamp ON llm_call_logs(user_id, timestamp DESC);
  CREATE INDEX idx_llm_logs_endpoint ON llm_call_logs(endpoint_name);
  CREATE INDEX idx_llm_logs_operation_type ON llm_call_logs(llm_operation_type);
  ```

## Monitoring & Alerting

Das System kann für folgende Monitoring-Zwecke genutzt werden:

1. **Error Rate Monitoring**: Überwachung der Fehlerrate pro Endpoint
2. **Performance Monitoring**: Durchschnittliche Response-Zeiten
3. **Usage Analytics**: Welche Features werden am meisten genutzt
4. **User Behavior**: Nutzungsverhalten einzelner User

## Migration

Die Tabelle wurde mit Alembic erstellt:
```bash
alembic revision --autogenerate -m "Add LLM call logging table v2"
alembic upgrade head
```

## Beispiel-Queries

### Top 10 Users nach LLM-Nutzung (letzte 7 Tage)
```sql
SELECT user_id, COUNT(*) as call_count
FROM llm_call_logs 
WHERE timestamp >= NOW() - INTERVAL '7 days'
GROUP BY user_id 
ORDER BY call_count DESC 
LIMIT 10;
```

### Durchschnittliche Response-Zeit pro Endpoint
```sql
SELECT endpoint_name, AVG(duration_ms) as avg_duration_ms
FROM llm_call_logs 
WHERE duration_ms IS NOT NULL 
GROUP BY endpoint_name 
ORDER BY avg_duration_ms DESC;
```

### Fehlerrate pro Operation Type
```sql
SELECT 
    llm_operation_type,
    COUNT(*) as total_calls,
    SUM(CASE WHEN success = false THEN 1 ELSE 0 END) as failed_calls,
    ROUND(SUM(CASE WHEN success = false THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as error_rate
FROM llm_call_logs 
WHERE llm_operation_type IS NOT NULL 
GROUP BY llm_operation_type 
ORDER BY error_rate DESC;
``` 