#!/usr/bin/env python3
"""
Workout-Generation Skript mit Unterstützung für minimal und compressed Versionen.
Generiert ein Workout mit strukturiertem JSON und Markdown Output.
"""
from pathlib import Path
import asyncio
import json
import time
from datetime import datetime
from uuid import UUID
from typing import Optional, Union

from utils.script_setup import setup_environment, get_standalone_session

# Setup environment before importing app modules
setup_environment()

# Import app modules after environment setup
from app.llm.workout_generation_v1.versions.minimal.service import (
    generate_minimal_workout_with_structure,
    MinimalWorkoutInput,
    MinimalWorkoutOutput,
)

from app.llm.workout_generation_v1.versions.compressed_20250731.service import (
    generate_compressed_workout,
    CompressedWorkoutInput,
    CompressedWorkoutOutput,
    parse_compressed_workout_to_db_models,
)
from app.llm.workout_generation_v1.versions.compressed_20250731.schemas import CompactWorkoutSchema

from app.models.workout_model import Workout
from app.models.block_model import Block
from sqlalchemy.ext.asyncio import AsyncSession


# ===== KONFIGURATION =====
USER_ID = "df668bed-9092-4035-82fa-c68e6fa2a8ff"  # UUID des Users
PROFILE_ID = 33956  # ID des Training Profiles (kann None sein)
USER_PROMPT = "Bitte plane für mich ein gutes Home Workout mit einer 24kg Kettlebell und einem Türreck für heute Abend."
SAVE_TO_FILE = True
OUTPUT_DIR = Path(__file__).parent / "output"


async def save_workout_outputs(
    workout_output: Union[MinimalWorkoutOutput, CompressedWorkoutOutput],
    full_prompt: str,
    user_id: UUID,
    user_prompt: str,
    profile_id: Optional[int],
    output_dir: Path
):
    """
    Speichert die Workout-Outputs in verschiedenen Formaten.
    
    Args:
        workout_output: Das generierte Workout
        full_prompt: Der vollständige LLM Prompt
        user_id: User ID
        user_prompt: Benutzer-Anfrage
        profile_id: Optional Training Profile ID
        output_dir: Output-Verzeichnis
    """
    output_dir.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    
    # Timing-Zusammenfassung
    timing_summary = f"""
⏱️  **PERFORMANCE ANALYSE:**
- **Workout-Generation:** {workout_output.generation_time:.2f}s
- **Übungen:** {workout_output.exercise_count}
- **Prompt Version:** {workout_output.prompt_version}
"""
    
    token_info = f"\n- **Token Reduktion:** {workout_output.token_reduction}" if hasattr(workout_output, 'token_reduction') else ""
    
    # 1. Speichere strukturiertes Workout als JSON
    workout_json_data = {
        "metadata": {
            "user_id": str(user_id),
            "profile_id": profile_id,
            "user_prompt": user_prompt,
            "generation_time": workout_output.generation_time,
            "exercise_count": workout_output.exercise_count,
            "prompt_version": workout_output.prompt_version,
            "timestamp": datetime.now().isoformat(),
        },
        "workout": (
            workout_output.workout.model_dump() if workout_output.workout else None
        ),
    }
    
    if hasattr(workout_output, 'token_reduction'):
        workout_json_data["metadata"]["token_reduction"] = workout_output.token_reduction
    
    json_file = output_dir / f"workout_{timestamp}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(workout_json_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 JSON Workout gespeichert: {json_file}")
    
    # 2. Speichere Markdown Workout
    workout_content = f"""# Generiertes Workout
**User ID:** {user_id}
**Profile ID:** {profile_id}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {user_prompt}

{timing_summary}{token_info}

---

{workout_output.markdown_workout}
"""
    
    markdown_file = output_dir / f"workout_{timestamp}.md"
    with open(markdown_file, "w", encoding="utf-8") as f:
        f.write(workout_content)
    
    print(f"💾 Markdown Workout gespeichert: {markdown_file}")
    
    # 3. Speichere den vollständigen Prompt
    prompt_content = f"""# Vollständiger LLM Prompt

**User ID:** {user_id}
**Profile ID:** {profile_id}
**Datum:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**User Prompt:** {user_prompt}

{timing_summary}{token_info}

---

{full_prompt}
"""
    
    prompt_file = output_dir / f"prompt_{timestamp}.md"
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(prompt_content)
    
    print(f"💾 Prompt gespeichert: {prompt_file}")


async def save_workout_to_database(
    db: AsyncSession,
    workout_schema: Union[CompactWorkoutSchema, MinimalWorkoutOutput],
    user_id: UUID,
    training_plan_id: Optional[int] = None
) -> Workout:
    """
    Speichert das generierte Workout in der Datenbank.
    
    Args:
        db: Database session
        workout_schema: Das generierte Workout Schema
        user_id: User ID
        training_plan_id: Optional training plan ID
        
    Returns:
        Das gespeicherte Workout mit ID
    """
    # Check if it's a CompactWorkoutSchema (compressed version)
    if hasattr(workout_schema, 'blocks'):
        workout = await parse_compressed_workout_to_db_models(
            workout_schema=workout_schema,
            user_id=user_id,
            training_plan_id=training_plan_id
        )
    else:
        # For minimal version, we'd need a different parser
        raise NotImplementedError("Database save for minimal version not yet implemented")
    
    # Add to session and commit
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    
    # Load blocks and exercises eagerly for counting
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    
    workout_with_blocks = await db.execute(
        select(Workout)
        .where(Workout.id == workout.id)
        .options(
            selectinload(Workout.blocks)
            .selectinload(Block.exercises)
        )
    )
    workout = workout_with_blocks.scalar_one()
    
    print(f"✅ Workout in Datenbank gespeichert mit ID: {workout.id}")
    return workout


async def generate_minimal_workout(
    user_id: UUID,
    user_prompt: str,
    profile_id: Optional[int] = None,
    save_to_file: bool = True,
    output_dir: Path = OUTPUT_DIR,
) -> MinimalWorkoutOutput:
    """
    Generiert ein Workout mit der minimalen Version.
    
    Args:
        user_id: UUID des Users
        user_prompt: Benutzer-Anfrage
        profile_id: Optional Training Profile ID
        save_to_file: Ob die Dateien gespeichert werden sollen
        output_dir: Verzeichnis für die Output-Dateien
        
    Returns:
        MinimalWorkoutOutput
    """
    print("📊 Starte Workout-Generation (Minimal Version)...")
    
    input_data = MinimalWorkoutInput(
        user_id=user_id,
        user_prompt=user_prompt,
        profile_id=profile_id
    )
    
    # Note: The minimal version still uses the old API with db parameter
    # TODO: Update minimal version to manage its own session internally
    async with get_standalone_session() as db:
        full_prompt, workout_output = await generate_minimal_workout_with_structure(
            db=db, input_data=input_data
        )
    
    print("✅ Workout erfolgreich generiert!")
    print(f"✅ Generation Zeit: {workout_output.generation_time:.2f}s")
    
    if save_to_file:
        await save_workout_outputs(
            workout_output, full_prompt, user_id, user_prompt, profile_id, output_dir
        )
    
    return workout_output


async def generate_compressed_workout_array(
    user_id: UUID,
    user_prompt: str,
    profile_id: Optional[int] = None,
    save_to_file: bool = True,
    save_to_database: bool = False,
    output_dir: Path = OUTPUT_DIR,
) -> CompressedWorkoutOutput:
    """
    Generiert ein Workout mit der compressed Array-basierten Version.
    
    Args:
        user_id: UUID des Users
        user_prompt: Benutzer-Anfrage
        profile_id: Optional Training Profile ID
        save_to_file: Ob die Dateien gespeichert werden sollen
        save_to_database: Ob das Workout in der Datenbank gespeichert werden soll
        output_dir: Verzeichnis für die Output-Dateien
        
    Returns:
        CompressedWorkoutOutput
    """
    print("📊 Starte Workout-Generation (Compressed Array-based Version)...")
    
    input_data = CompressedWorkoutInput(
        user_id=user_id,
        user_prompt=user_prompt,
        profile_id=profile_id
    )
    
    # Generate workout (this will use its own session internally)
    full_prompt, workout_output = await generate_compressed_workout(
        input_data=input_data
    )
    
    print("✅ Workout erfolgreich generiert!")
    print(f"✅ Generation Zeit: {workout_output.generation_time:.2f}s")
    print(f"✅ Token Reduktion: {workout_output.token_reduction}")
    
    # Save to database if requested (separate session)
    if save_to_database and workout_output.workout:
        async with get_standalone_session() as db:
            saved_workout = await save_workout_to_database(
                db=db,
                workout_schema=workout_output.workout,
                user_id=user_id,
                training_plan_id=None  # Don't use profile_id as training_plan_id
            )
            print(f"📊 Workout Name: {saved_workout.name}")
            print(f"📊 Workout ID: {saved_workout.id}")
            print(f"📊 Anzahl Blöcke: {len(saved_workout.blocks)}")
            total_exercises = sum(len(block.exercises) for block in saved_workout.blocks)
            print(f"📊 Anzahl Übungen: {total_exercises}")
    
    if save_to_file:
        await save_workout_outputs(
            workout_output, full_prompt, user_id, user_prompt, profile_id, output_dir
        )
    
    return workout_output


# ===== MAIN =====
async def main():
    start_time = time.time()
    
    print("🚀 S3SSIONS Workout Generation")
    print("=" * 50)
    
    if USER_ID == "your-user-uuid-here":
        print("❌ Bitte USER_ID im Skript konfigurieren!")
        return
    
    user_id_uuid = UUID(USER_ID)
    
    try:
        # ========================================
        # HIER EINE DER BEIDEN FUNKTIONEN NUTZEN:
        # ========================================
        
        # Option 1: Minimal Version
        # workout_output = await generate_minimal_workout(
        #     user_id=user_id_uuid,
        #     user_prompt=USER_PROMPT,
        #     profile_id=PROFILE_ID,
        #     save_to_file=SAVE_TO_FILE,
        #     output_dir=OUTPUT_DIR
        # )
        
        # Option 2: Compressed Array-based Version (90% weniger Tokens)
        workout_output = await generate_compressed_workout_array(
            user_id=user_id_uuid,
            user_prompt=USER_PROMPT,
            profile_id=PROFILE_ID,
            save_to_file=SAVE_TO_FILE,
            save_to_database=True,  # Enable database save
            output_dir=OUTPUT_DIR
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
        print(f"📦 Workout Name: {workout_output.workout.name if workout_output.workout else 'N/A'}")
        print(f"🎯 Fokus: {workout_output.workout.focus if workout_output.workout else 'N/A'}")
        
        if hasattr(workout_output, 'token_reduction'):
            print(f"💎 Token Reduktion: {workout_output.token_reduction}")
        
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