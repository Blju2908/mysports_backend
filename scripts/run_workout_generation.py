#!/usr/bin/env python3
"""
Einfaches Skript zur Workout-Generation mit der minimalen Version.
Generiert ein Workout als Markdown ohne Parsing.
"""
from pathlib import Path
import asyncio
import time
from datetime import datetime
from uuid import UUID

from utils.script_setup import setup_environment, get_standalone_session

setup_environment()

from app.llm.workout_generation_v1.versions.minimal.service import (
    generate_minimal_workout,
    MinimalWorkoutInput,
)

# ===== KONFIGURATION =====
USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # UUID des Users
PROFILE_ID = 33956  # ID des Training Profiles (kann None sein)
USER_PROMPT = "Bitte plane für mich ein gutes Home Workout mit einer 24kg Kettlebell und einem Türreck für heute Abend."
SAVE_TO_FILE = True
OUTPUT_DIR = Path(__file__).parent / "output"


# ===== MAIN =====
async def main():
    start_time = time.time()

    print("🚀 S3SSIONS Workout Generation mit DB-Kontext")
    print("=" * 50)

    if USER_ID == "your-user-uuid-here":
        print("❌ Bitte USER_ID im Skript konfigurieren!")
        return

    user_id_uuid = UUID(USER_ID)

    # Erstelle Input-Daten für den Service
    input_data = MinimalWorkoutInput(
        user_id=user_id_uuid, user_prompt=USER_PROMPT, profile_id=PROFILE_ID
    )

    try:
        print("📊 Starte Workout-Generation (Minimal Version)...")

        # Nutze die minimale Version für schnelle Markdown-Generation
        async with get_standalone_session() as db:
            full_prompt, markdown_workout, generation_time = (
                await generate_minimal_workout(db=db, input_data=input_data)
            )

        print("✅ Workout erfolgreich generiert!")
        print(f"✅ Generation Zeit: {generation_time:.2f}s")

        # === ZEIT MESSUNG ENDE ===
        end_time = time.time()
        total_duration = end_time - start_time

        # Timing-Zusammenfassung
        timing_summary = f"""
⏱️  **PERFORMANCE ANALYSE:**
- **Workout-Generation:** {generation_time:.2f}s
- **Gesamtzeit:** {total_duration:.2f}s
"""

        print(timing_summary)

        # --- Speichere die Dateien ---
        if SAVE_TO_FILE:
            OUTPUT_DIR.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

            # 1. Speichere den vollständigen Prompt
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

            # 2. Speichere das Workout als Markdown
            workout_content = f"""# Generiertes Workout

**User ID:** {USER_ID}
**Profile ID:** {PROFILE_ID}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {USER_PROMPT}

{timing_summary}

---

{markdown_workout}
"""

            workout_file = OUTPUT_DIR / f"workout_{timestamp}.md"
            with open(workout_file, "w") as f:
                f.write(workout_content)

            print(f"💾 Workout gespeichert: {workout_file}")

    except Exception as e:
        print(f"❌ Fehler bei der Workout Generation: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
