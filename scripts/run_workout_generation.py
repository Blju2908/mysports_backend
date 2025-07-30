#!/usr/bin/env python3
import os
from pathlib import Path
import asyncio
import time
from datetime import datetime
from uuid import UUID
from sqlalchemy import select

from utils.script_setup import setup_environment, get_standalone_session
setup_environment()

from app.llm.workout_generation.workout_generation_service import (
    WorkoutGenerationInput,
    generate_workout_complete
)

# ===== KONFIGURATION =====
USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # UUID des Users
PROFILE_ID = 33956  # ID des Training Profiles (kann None sein)
USER_PROMPT = "Bitte plane für mich ein gutes Home Workout mit einer 24kg Kettlebell und einem Türreck für heute Abend."
SAVE_TO_FILE = True
OUTPUT_DIR = Path(__file__).parent / "output"

# ===== MAIN =====
async def main():
    # === ZEIT MESSUNG START ===
    start_time = time.time()
    
    print("🚀 S3SSIONS Workout Generation mit DB-Kontext")
    print("=" * 50)
    
    if USER_ID == "your-user-uuid-here":
        print("❌ Bitte USER_ID im Skript konfigurieren!")
        return
    
    user_id_uuid = UUID(USER_ID)
    
    # Erstelle Input-Daten für den Service
    input_data = WorkoutGenerationInput(
        user_id=user_id_uuid,
        user_prompt=USER_PROMPT,
        profile_id=PROFILE_ID
    )
    
    # Timing-Variablen
    generation_start = time.time()
    
    try:
        print("📊 Starte Workout-Generation mit Service...")
        
        # Nutze den gemeinsamen Service
        async with get_standalone_session() as db:
            full_prompt, compact_workout_schema, generation_data = await generate_workout_complete(
                db=db,
                input_data=input_data
            )
        
        generation_end = time.time()
        generation_duration = generation_end - generation_start
        
        print("✅ Workout erfolgreich generiert!")
        print(f"✅ Training Plan ID: {generation_data.training_plan_id}")
        if generation_data.environment_profile:
            print(f"✅ Training Profile geladen (ID: {PROFILE_ID})")
        
        exercise_count = len(generation_data.exercise_library.splitlines()) if generation_data.exercise_library else 0
        print(f"✅ Exercise Library: {exercise_count} Übungen")
        
        # === ZEIT MESSUNG ENDE ===
        end_time = time.time()
        total_duration = end_time - start_time
        
        # Timing-Zusammenfassung
        timing_summary = f"""
⏱️  **PERFORMANCE ANALYSE:**
- **Workout-Generation (komplett):** {generation_duration:.2f}s
- **Gesamtzeit:** {total_duration:.2f}s
"""
        
        print(timing_summary)
        
        # --- STEP 4: Speichere alle Dateien ---
        import json
        
        if SAVE_TO_FILE:
            OUTPUT_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            
            # 1. Speichere den vollständigen Prompt mit Timing
            prompt_file = OUTPUT_DIR / f"prompt_{timestamp}.md"
            prompt_content = f"""# Vollständiger LLM Prompt

**User ID:** {USER_ID}
**Profile ID:** {PROFILE_ID}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {USER_PROMPT}

{timing_summary}

---

{full_prompt}
"""
            
            with open(prompt_file, "w") as f:
                f.write(prompt_content)
            
            print(f"💾 Prompt gespeichert: {prompt_file}")
            
            # 2. Speichere das komplette Workout Schema mit Timing
            schema_content = f"""# Komplettes Workout Schema

**User ID:** {USER_ID}
**Profile ID:** {PROFILE_ID}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {USER_PROMPT}

{timing_summary}

## Workout Schema (JSON)

```json
{json.dumps(compact_workout_schema.model_dump(), indent=2, ensure_ascii=False)}
```
"""
            
            schema_file = OUTPUT_DIR / f"workout_schema_{timestamp}.md"
            with open(schema_file, "w") as f:
                f.write(schema_content)
            
            print(f"💾 Workout Schema gespeichert: {schema_file}")
                        
    except Exception as e:
        print(f"❌ Fehler bei der Workout Generation: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())