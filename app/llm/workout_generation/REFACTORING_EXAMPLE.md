# Refactoring-Beispiel: Endpoint mit neuem Service

## Vorher (Redundanter Code im Endpoint):

```python
async def generate_workout_background(workout_id: int, user_id: str, request_data: CreateWorkoutRequest, log_id: int):
    # --- STEP 1: Gather all necessary data in one DB session ---
    formatted_training_plan = None
    summarized_history_str = None
    exercise_library_str = ""
    training_plan_id_for_saving = None

    async with create_session() as db:
        # Load and format TrainingPlan
        training_plan_db_obj = await db.scalar(
            select(TrainingPlan).where(TrainingPlan.user_id == user_id_uuid)
        )
        if training_plan_db_obj:
            training_plan_id_for_saving = training_plan_db_obj.id
            formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)

        # Load, summarize, and format Training History
        raw_training_history = await get_latest_workouts_with_details(
            db=db, user_id=user_id_uuid, number_of_workouts=10
        )
        if raw_training_history:
            summarized_history_str = summarize_training_history(raw_training_history)

        # Load exercise library
        exercise_library_str = await get_all_exercises_for_prompt(db)

    # --- STEP 2: Execute LLM chain ---
    compact_workout_schema = await execute_workout_generation_sequence_v2(
        training_plan_str=formatted_training_plan,
        training_history_str=summarized_history_str,
        user_prompt=request_data.prompt,
        exercise_library_str=exercise_library_str,
    )
    
    # ... Rest der Funktion (DB-Speicherung, Logging)
```

## Nachher (Mit neuem Service):

```python
async def generate_workout_background(workout_id: int, user_id: str, request_data: CreateWorkoutRequest, log_id: int):
    from app.llm.workout_generation.workout_generation_service import WorkoutGenerationInput, generate_workout_complete
    
    # Input-Daten erstellen
    input_data = WorkoutGenerationInput(
        user_id=UUID(user_id),
        user_prompt=request_data.prompt,
        profile_id=request_data.profile_id,  # Falls im Request vorhanden
        session_duration=request_data.session_duration  # Falls im Request vorhanden
    )
    
    # Komplette Workout-Generation mit Service
    async with create_session() as db:
        full_prompt, compact_workout_schema, generation_data = await generate_workout_complete(
            db=db,
            input_data=input_data
        )
    
    # training_plan_id für DB-Speicherung
    training_plan_id_for_saving = generation_data.training_plan_id
    
    # ... Rest der Funktion (DB-Speicherung, Logging) bleibt gleich
```

## Vorteile der Refactoring:

1. **🔄 DRY Prinzip:** Keine Code-Duplikation zwischen Skript und Endpoint
2. **🧪 Testbarkeit:** Service kann isoliert getestet werden
3. **📦 Modulärität:** Klare Trennung von Datenabfrage und LLM-Generation
4. **🔧 Wartbarkeit:** Änderungen nur an einer Stelle nötig
5. **📊 Konsistenz:** Identisches Verhalten zwischen Skript und Endpoint

## Aktuelle Situation:

- ✅ **Skript:** Nutzt bereits den neuen Service
- ⏳ **Endpoint:** Könnte refactored werden (optional)
- ✅ **Service:** Eliminiert Redundanz erfolgreich