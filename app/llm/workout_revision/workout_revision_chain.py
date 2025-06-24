from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.llm.utils.llm_documentation import document_llm_session, document_llm_input, document_llm_output
import json
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path

PROMPT_FILE_FREEFORM = "workout_revision_prompt_step1.md"  # New prompt for creative/free-form revision
PROMPT_FILE_STRUCTURE = "workout_revision_prompt_step2.md"  # New prompt for structure conversion

# ============================================================
# Two-step workout revision: Step 1 (Free-form) + Step 2 (Structured)
# ============================================================

async def revise_workout_two_step(
    existing_workout: Dict[str, Any],
    user_feedback: str,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None
) -> WorkoutSchema:
    """
    Überarbeitet ein Workout in zwei Schritten:
    1. Freie Revision für Kreativität und Flexibilität
    2. Strukturierung in WorkoutSchema mit kleinem, schnellem LLM
    """
    # Step 1: Freie Workout-Revision
    freeform_revision_text = await revise_workout_freeform(
        existing_workout, user_feedback, training_plan, training_history
    )
    
    # Step 2: Strukturierung des freien Revisions-Texts
    structured_workout = await convert_revision_to_schema(freeform_revision_text)
    
    return structured_workout

async def convert_revision_to_schema(freeform_revision_text: str) -> WorkoutSchema:
    """
    Konvertiert freien Revisions-Text in strukturiertes WorkoutSchema.
    Nutzt ein kleines, schnelles LLM für die Strukturierung.
    """
    try:
        # Load structure conversion prompt
        prompt_path = Path(__file__).parent / PROMPT_FILE_STRUCTURE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()
        
        formatted_prompt = prompt_template_content.format(
            freeform_revision=freeform_revision_text
        )
        
        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        
        # Nutze kleines, schnelles Modell für Strukturierung
        llm = ChatOpenAI(
            model="gpt-4.1-mini", 
            api_key=OPENAI_API_KEY,
            temperature=0.1  # Niedrige Temperatur für konsistente Strukturierung
        )
        
        # LangChain's structured output für automatische Schema-Validierung
        structured_llm = llm.with_structured_output(WorkoutSchema)
        
        print("Converting freeform revision to structured workout schema...")
        structured_workout = await structured_llm.ainvoke(formatted_prompt)
        print("Successfully converted revision to structured schema")
        
        # Dokumentiere Input/Output für Step 2
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)
            
            # Input dokumentieren
            input_path = out_dir / f"{ts}_revision_structure_conversion_input.md"
            input_path.write_text(freeform_revision_text, encoding="utf-8")
            
            # Output dokumentieren
            output_path = out_dir / f"{ts}_revision_structure_conversion_output.json"
            output_path.write_text(structured_workout.model_dump_json(indent=2), encoding="utf-8")
            
            print(f"[LLM_DOCS] Revision structure conversion documented: {input_path} -> {output_path}")
        except Exception as e:  # noqa: BLE001
            print(f"[LLM_DOCS] Could not document revision structure conversion: {e}")
        
        return structured_workout

    except Exception as e:
        print(f"Error in convert_revision_to_schema: {e}")
        import traceback
        traceback.print_exc()
        raise

async def revise_workout_freeform(
    existing_workout: Dict[str, Any],
    user_feedback: str,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None
) -> str:
    """
    Überarbeitet ein Workout mit LLM in freier Textform.
    """
    try:
        # Load the Prompt File        
        prompt_path = Path(__file__).parent / PROMPT_FILE_FREEFORM
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        # Convert existing workout to JSON string for the prompt
        existing_workout_json = json.dumps(existing_workout, indent=2, ensure_ascii=False, default=str)

        # Ensure default empty strings if None, to avoid issues with .format
        formatted_prompt = prompt_template_content.format(
            existing_workout=existing_workout_json,
            user_feedback=user_feedback,
            training_plan=training_plan if training_plan is not None else "",
            training_history=training_history if training_history is not None else "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        reasoning = {
            "effort": "medium",
            "summary": None
        }
        
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY, use_responses_api=True, model_kwargs={"reasoning": reasoning})

        # Add reasoning to the prompt
        await document_llm_input(formatted_prompt, "workout_revision_prompt_freeform.md")

        print("Sending request to OpenAI API (freeform revision)…")
        response = await llm.ainvoke(formatted_prompt)
        print("Received response from OpenAI API (freeform revision)")

        # Extract actual text content from LangChain response
        if hasattr(response, 'content'):
            if isinstance(response.content, list):
                # Handle list content (e.g., from structured responses)
                freeform_text = ""
                for item in response.content:
                    if hasattr(item, 'text'):
                        freeform_text += item.text
                    elif isinstance(item, dict) and 'text' in item:
                        freeform_text += item['text']
                    else:
                        freeform_text += str(item)
            else:
                freeform_text = response.content
        else:
            freeform_text = str(response)

        # Dokumentiere Output (Markdown)
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / f"{ts}_workout_revision_freeform_output.md"
            out_path.write_text(freeform_text, encoding="utf-8")
            print(f"[LLM_DOCS] Free-form revision output documented: {out_path}")
        except Exception as e:  # noqa: BLE001
            print(f"[LLM_DOCS] Could not document free-form revision output: {e}")

        return freeform_text

    except Exception as e:
        print(f"Error in revise_workout_freeform: {e}")
        import traceback
        traceback.print_exc()
        raise

# ============================================================
# Legacy function for backward compatibility
# ============================================================

async def revise_workout(
    existing_workout: Dict[str, Any],
    user_feedback: str,
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None
) -> WorkoutSchema:
    """
    Legacy function - delegates to new two-step process
    """
    return await revise_workout_two_step(existing_workout, user_feedback, training_plan, training_history) 