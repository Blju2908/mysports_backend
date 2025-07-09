from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Literal
from pathlib import Path
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.training_plan_model import TrainingPlan
from app.llm.workout_generation.exercise_filtering_service import (
    get_filtered_exercises_for_user,
    get_all_exercises_for_prompt,
)

# 2-Step Approach
PROMPT_FILE_FREEFORM = "workout_generation_prompt_step1.md"
PROMPT_FILE_STRUCTURE = "workout_generation_prompt_step2.md"

# Combinded Prompt
PROMPT_FILE_COMBINED = "workout_generation_prompt_combined.md"


# New workout generation function
async def execute_workout_generation_sequence(
    training_plan_obj: Optional[TrainingPlan] = None,
    training_plan_str: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
    db: Optional[AsyncSession] = None,
    use_exercise_filtering: bool = False,
) -> WorkoutSchema:
    """
    Args:
        training_plan_obj: TrainingPlan Object für Exercise Filtering
        training_plan_str: Formatierter TrainingPlan String für LLM
        training_history: Training History String
        user_prompt: User Prompt
        db: Database Session (nur für Exercise Filtering nötig)
        use_exercise_filtering: Wenn True, filtert Übungen aus DB
        approach: "one_step" oder "two_step" Generation
    """

    _start_total = datetime.now()
    approach = "two_step"

    # Prepare exercise context by deciding which exercise list to use
    exercise_library = None
    if use_exercise_filtering and training_plan_obj and db:
        try:
            print("🔍 Using DB Exercise Filtering...")
            exercise_library = await get_filtered_exercises_for_user(
                training_plan=training_plan_obj, db=db, user_prompt=user_prompt
            )
            if exercise_library:
                print(
                    f"✅ Using {len(exercise_library.splitlines())} filtered exercises from DB"
                )
            else:
                print(
                    "⚠️ DB filtering failed or returned no exercises, falling back to full DB list."
                )
        except Exception as e:
            print(f"Error in get_filtered_exercises_for_user: {e}")
            exercise_library = None

    if exercise_library is None:
        exercise_library = await get_all_exercises_for_prompt(db)

    # Choose generation method based on approach
    if approach == "one_step":
        print("Using enhanced one-step approach")
        _start_combined = datetime.now()
        structured_workout = await generate_workout_direct_to_schema_enhanced(
            training_plan=training_plan_str,
            training_history=training_history,
            user_prompt=user_prompt,
            exercise_library=exercise_library,
        )
        _combined_duration = (datetime.now() - _start_combined).total_seconds()
        print(f"⏱️ combined_approach total duration: {_combined_duration:.1f}s")

        _total_duration = (datetime.now() - _start_total).total_seconds()
        print(f"⏱️ TOTAL workout_generation duration: {_total_duration:.1f}s")

        return structured_workout
    else:
        print("Using enhanced two-step approach")
        _start_step1 = datetime.now()
        freeform_text = await generate_freeform_workout_enhanced(
            training_plan=training_plan_str,
            training_history=training_history,
            user_prompt=user_prompt,
            exercise_library=exercise_library,
        )
        _step1_duration = (datetime.now() - _start_step1).total_seconds()
        print(f"⏱️ step1_freeform total duration: {_step1_duration:.1f}s")

        _start_step2 = datetime.now()
        structured_workout = await convert_freeform_workout_to_schema(freeform_text)
        _step2_duration = (datetime.now() - _start_step2).total_seconds()
        print(f"⏱️ step2_structure total duration: {_step2_duration:.1f}s")

        _total_duration = (datetime.now() - _start_total).total_seconds()
        print(f"⏱️ TOTAL workout_generation duration: {_total_duration:.1f}s")

        return structured_workout


# One-Step Approach
async def generate_workout_direct_to_schema_enhanced(
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
    exercise_library: Optional[str] = None,
) -> WorkoutSchema:
    """Enhanced one-step generation using a dynamic exercise library."""

    try:
        prompt_path = (
            Path(__file__).parent / "prompts" / "workout_generation_prompt_combined.md"
        )

        # Load training principles
        training_principles_path = (
            Path(__file__).parent / "prompts" / "training_principles_base.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        with open(training_principles_path, "r", encoding="utf-8") as f:
            training_principles_content = f.read()

        # Format prompt with the dynamic exercise library and training principles
        formatted_prompt = prompt_template_content.format(
            training_plan=training_plan or "",
            training_history=training_history or "",
            user_prompt=user_prompt or "",
            exercise_library=exercise_library or "",
            training_principles=training_principles_content,
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # LLM Call
        # llm = get_llm_model(provider="google", model="gemini-2.5-flash")
        llm = get_llm_model(provider="openai", model="o4-mini")
        structured_llm = llm.with_structured_output(WorkoutSchema)

        print("Sending enhanced direct-to-schema request…")
        _start = datetime.now()
        structured_workout = await structured_llm.ainvoke(formatted_prompt)
        _duration = (datetime.now() - _start).total_seconds()
        print(f"⏱️ direct_schema LLM duration: {_duration:.1f}s")

        # Document output
        suffix = (
            "db_filtered"
            if "Oberschenkel-Vorderseite" in (exercise_library or "")
            else "default"
        )
        _document_llm_interaction(
            stage="direct_schema",
            prompt=formatted_prompt,
            response=structured_workout,
            suffix=suffix,
        )

        return structured_workout

    except Exception as e:
        print(f"Error in enhanced direct-to-schema generation: {e}")
        raise


async def generate_freeform_workout_enhanced(
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
    exercise_library: Optional[str] = None,
) -> str:
    """Enhanced freeform generation using a dynamic exercise library."""

    try:
        # Use a single prompt file for the freeform step
        prompt_path = (
            Path(__file__).parent / "prompts" / "workout_generation_prompt_step1.md"
        )
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt file not found at {prompt_path}")
            
        # Load training principles
        training_principles_path = (
            Path(__file__).parent / "prompts" / "training_principles_base.md"
        )

        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        with open(training_principles_path, "r", encoding="utf-8") as f:
            training_principles_content = f.read()

        # Format prompt with the dynamic exercise library and training principles
        formatted_prompt = prompt_template_content.format(
            training_plan=training_plan or "",
            training_history=training_history or "",
            user_prompt=user_prompt or "",
            exercise_library=exercise_library or "",
            training_principles=training_principles_content,
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # LLM Call
        llm = get_llm_model(provider="openai", model="gpt-4o")
        # llm = get_llm_model(provider="google", model="gemini-2.5-flash")
        _start = datetime.now()
        response = await llm.ainvoke(formatted_prompt)
        _duration = (datetime.now() - _start).total_seconds()
        print(f"⏱️ freeform LLM duration: {_duration:.1f}s")

        # Extract content
        if hasattr(response, "content"):
            freeform_text = (
                response.content
                if isinstance(response.content, str)
                else str(response.content)
            )
        else:
            freeform_text = str(response)

        # Document output
        suffix = (
            "db_filtered"
            if "Oberschenkel-Vorderseite" in (exercise_library or "")
            else "default"
        )
        _document_llm_interaction(
            stage="freeform",
            prompt=formatted_prompt,
            response=freeform_text,
            suffix=suffix,
        )

        return freeform_text

    except Exception as e:
        print(f"Error in enhanced freeform generation: {e}")
        raise


# Two-Step Approach - Step 2
async def convert_freeform_workout_to_schema(freeform_text: str) -> WorkoutSchema:
    """
    ✅ OPTIMIZED: Konvertiert freien Workout-Text in strukturiertes WorkoutSchema.
    Nutzt LangChain's structured output für automatische JSON-Konvertierung.
    """
    try:
        # Load structure conversion prompt
        prompt_path = Path(__file__).parent / "prompts" / PROMPT_FILE_STRUCTURE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        # Replace placeholder with freeform text (no cleaning needed)
        formatted_prompt = prompt_template_content.replace(
            "FREEFORM_WORKOUT_PLACEHOLDER", freeform_text
        )

        # Nutze kleines, schnelles Modell für Strukturierung
        PROVIDER = "google"
        llm = get_llm_model(provider=PROVIDER, model="gemini-2.5-flash")

        # ✅ LangChain's structured output für automatische JSON-Konvertierung
        structured_llm = llm.with_structured_output(WorkoutSchema)

        print("Converting freeform text to structured workout schema…")
        _start = datetime.now()
        structured_workout = await structured_llm.ainvoke(formatted_prompt)
        _duration = (datetime.now() - _start).total_seconds()
        print(f"⏱️ structure_conversion LLM duration: {_duration:.1f}s")

        # Document output
        _document_llm_interaction(
            stage="structure_conversion",
            prompt=formatted_prompt,
            response=structured_workout,
        )

        return structured_workout

    except Exception as e:
        print(f"Error in convert_freeform_to_schema: {e}")
        import traceback

        traceback.print_exc()
        raise


# Helper functions
def _document_llm_interaction(
    stage: str, prompt: str, response: "str | WorkoutSchema", suffix: str = ""
) -> None:
    """Schreibt Prompt und Response/Schema mit eindeutigem Zeitstempel auf die Platte.

    Args:
        stage: Kurze Kennzeichnung des Schritts, z.B. "freeform", "direct_schema", "structure_conversion".
        prompt: Der an das LLM gesendete Prompt-String.
        response: Die Antwort – kann Text oder ein WorkoutSchema sein.
        suffix: Optionaler Suffix wie "db_filtered" oder "default" für Unterscheidung.
    """

    try:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        label = f"{stage}{'_' + suffix if suffix else ''}"
        out_dir = Path(__file__).parent / "output"
        out_dir.mkdir(exist_ok=True)

        # Prompt immer als Markdown speichern
        prompt_path = out_dir / f"{ts}_{label}_prompt.md"
        prompt_path.write_text(prompt, encoding="utf-8")

        # Response als JSON wenn möglich, sonst Markdown
        if hasattr(response, "model_dump_json"):
            output_text = response.model_dump_json(indent=2)
            output_path = out_dir / f"{ts}_{label}_response.json"
        else:
            output_text = str(response)
            output_path = out_dir / f"{ts}_{label}_response.md"

        output_path.write_text(output_text, encoding="utf-8")
        print(f"[LLM_DOCS] Documented {label}: {prompt_path.name} & {output_path.name}")
    except Exception as e:
        print(f"[LLM_DOCS] Could not document {stage}: {e}")


def get_llm_model(provider: str, model: str):
    if provider == "openai":
        if model == "o4-mini":
            reasoning = {
                "effort": "medium",
                "summary": None
            }
            return ChatOpenAI(model=model, api_key=get_config().OPENAI_API_KEY2, use_responses_api=True, model_kwargs={"reasoning": reasoning})
        else:
            return ChatOpenAI(model=model, api_key=get_config().OPENAI_API_KEY2)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, api_key=get_config().ANTHROPIC_API_KEY)
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=model, google_api_key=get_config().GOOGLE_API_KEY
        )
