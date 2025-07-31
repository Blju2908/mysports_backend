#!/usr/bin/env python3
"""
Einfaches Skript zur Workout-Generation mit der minimalen Version.
Generiert ein Workout mit strukturiertem JSON und Markdown Output.
"""
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime
from uuid import UUID

from utils.script_setup import setup_environment, get_standalone_session

# Setup environment before importing app modules
setup_environment()

# Import app modules after environment setup
from app.llm.workout_generation_v1.versions.minimal.service import (
    generate_minimal_workout_with_structure,
    MinimalWorkoutInput,
    MinimalWorkoutOutput,
)

# ===== KONFIGURATION =====
USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # UUID des Users
PROFILE_ID = 33956  # ID des Training Profiles (kann None sein)
USER_PROMPT = "Bitte plane für mich ein gutes Home Workout mit einer 24kg Kettlebell und einem Türreck für heute Abend."
SAVE_TO_FILE = True
OUTPUT_DIR = Path(__file__).parent / "output"


async def generate_minimal_workout_with_exports(
    input_data: MinimalWorkoutInput,
    save_to_file: bool = True,
    output_dir: Path = OUTPUT_DIR,
) -> MinimalWorkoutOutput:
    """
    Generiert ein minimales Workout und exportiert sowohl JSON als auch Markdown.

    Args:
        input_data: Input-Daten für die Workout-Generation
        save_to_file: Ob die Dateien gespeichert werden sollen
        output_dir: Verzeichnis für die Output-Dateien

    Returns:
        MinimalWorkoutOutput: Vollständige strukturierte Workout-Daten
    """
    print("📊 Starte Workout-Generation (Minimal Version mit strukturiertem Output)...")

    async with get_standalone_session() as db:
        full_prompt, workout_output = await generate_minimal_workout_with_structure(
            db=db, input_data=input_data
        )

    print("✅ Workout erfolgreich generiert!")
    print(f"✅ Generation Zeit: {workout_output.generation_time:.2f}s")

    if save_to_file:
        output_dir.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

        # Timing-Zusammenfassung für Dateien
        timing_summary = f"""
⏱️  **PERFORMANCE ANALYSE:**
- **Workout-Generation:** {workout_output.generation_time:.2f}s
- **Übungen:** {workout_output.exercise_count}
- **Prompt Version:** {workout_output.prompt_version}
"""

        # 1. Speichere strukturiertes Workout als JSON
        workout_json_data = {
            "metadata": {
                "user_id": str(input_data.user_id),
                "profile_id": input_data.profile_id,
                "user_prompt": input_data.user_prompt,
                "generation_time": workout_output.generation_time,
                "exercise_count": workout_output.exercise_count,
                "prompt_version": workout_output.prompt_version,
                "timestamp": datetime.now().isoformat(),
            },
            "workout": (
                workout_output.workout.model_dump() if workout_output.workout else None
            ),
        }

        json_file = output_dir / f"workout_{timestamp}.json"
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(workout_json_data, f, indent=2, ensure_ascii=False)

        print(f"💾 JSON Workout gespeichert: {json_file}")

        # 2. Speichere Markdown Workout
        workout_content = f"""# Generiertes Workout
            **User ID:** {input_data.user_id}
            **Profile ID:** {input_data.profile_id}
            **Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
            **User Prompt:** {input_data.user_prompt}

            {timing_summary}

            ---

            {workout_output.markdown_workout}
            """

        markdown_file = output_dir / f"workout_{timestamp}.md"
        with open(markdown_file, "w", encoding="utf-8") as f:
            f.write(workout_content)

        print(f"💾 Markdown Workout gespeichert: {markdown_file}")

        # 3. Speichere den vollständigen Prompt
        prompt_content = f"""# Vollständiger LLM Prompt

**User ID:** {input_data.user_id}
**Profile ID:** {input_data.profile_id}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {input_data.user_prompt}

{timing_summary}

---

{full_prompt}
"""

        prompt_file = output_dir / f"prompt_{timestamp}.md"
        with open(prompt_file, "w", encoding="utf-8") as f:
            f.write(prompt_content)

        print(f"💾 Prompt gespeichert: {prompt_file}")

    return workout_output


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
        # Generiere Workout mit strukturiertem Output und Exports
        workout_output = await generate_minimal_workout_with_exports(
            input_data=input_data, save_to_file=SAVE_TO_FILE, output_dir=OUTPUT_DIR
        )

        # === ZEIT MESSUNG ENDE ===
        end_time = time.time()
        total_duration = end_time - start_time

        # Zusammenfassung
        print("\n" + "=" * 60)
        print("🎉 WORKOUT GENERATION ABGESCHLOSSEN")
        print("=" * 60)
        print(f"⏱️  Workout-Generation: {workout_output.generation_time:.2f}s")
        print(f"⏱️  Gesamtzeit: {total_duration:.2f}s")
        print(f"🏋️  Übungen insgesamt: {workout_output.exercise_count}")
        print(
            f"📦 Workout Name: {workout_output.workout.name if workout_output.workout else 'N/A'}"
        )
        print(
            f"🎯 Fokus: {workout_output.workout.focus if workout_output.workout else 'N/A'}"
        )

        if SAVE_TO_FILE:
            print("\n📁 Exportierte Dateien:")
            print("   • JSON: Strukturierte Workout-Daten")
            print("   • Markdown: Human-readable Format")
            print("   • Prompt: Vollständiger LLM Input")

    except Exception as e:
        print(f"❌ Fehler bei der Workout Generation: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
