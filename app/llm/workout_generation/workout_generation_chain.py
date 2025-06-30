from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from app.llm.utils.llm_documentation import document_llm_input, document_llm_output
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.core.config import get_config
from datetime import datetime
from typing import Optional
from pathlib import Path

PROMPT_FILE = "workout_generation_prompt.md"
PROMPT_FILE_FREEFORM = "workout_generation_prompt_step1.md"  # New prompt for the creative/free-form step-1 generation
PROMPT_FILE_STRUCTURE = "workout_generation_prompt_step2.md"  # New prompt for structure conversion

def create_anthropic_llm():
    config = get_config()

    llm = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        api_key=config.ANTHROPIC_API_KEY,
        max_retries=2
    )
    return llm

# ============================================================
# Two-step workout generation: Step 1 (Free-form) + Step 2 (Structured)
# ============================================================

async def generate_workout_two_step(
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None
) -> WorkoutSchema:
    """
    Generiert ein Workout in zwei Schritten:
    1. Freie Textgenerierung für Kreativität und Flexibilität
    2. Strukturierung in WorkoutSchema mit kleinem, schnellem LLM
    """
    # Step 1: Freie Workout-Generierung
    freeform_text = await generate_workout(training_plan, training_history, user_prompt)
    
    # Step 2: Strukturierung des freien Texts
    structured_workout = await convert_freeform_to_schema(freeform_text)
    
    return structured_workout

async def convert_freeform_to_schema(freeform_text: str) -> WorkoutSchema:
    """
    ✅ OPTIMIZED: Konvertiert freien Workout-Text in strukturiertes WorkoutSchema.
    Nutzt LangChain's structured output für automatische JSON-Konvertierung.
    """
    try:
        # Load structure conversion prompt
        prompt_path = Path(__file__).parent / PROMPT_FILE_STRUCTURE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()
        
        # Replace placeholder with freeform text (no cleaning needed)
        formatted_prompt = prompt_template_content.replace(
            "FREEFORM_WORKOUT_PLACEHOLDER", 
            freeform_text
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
        
        # ✅ LangChain's structured output für automatische JSON-Konvertierung
        structured_llm = llm.with_structured_output(WorkoutSchema)
        
        print("Converting freeform text to structured workout schema...")
        structured_workout = await structured_llm.ainvoke(formatted_prompt)
        print("Successfully converted to structured schema")
        
        # ✅ FIXED: Document JSON output without ensure_ascii
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)
            
            # ✅ Input dokumentieren (nur wenn anders als freeform_output)
            input_path = out_dir / f"{ts}_structure_conversion_input.md"
            input_path.write_text(freeform_text, encoding="utf-8")
            
            # ✅ FIXED: JSON Output ohne ensure_ascii Parameter
            output_path = out_dir / f"{ts}_structure_conversion_output.json"
            json_content = structured_workout.model_dump_json(indent=2)  # Removed ensure_ascii=False
            output_path.write_text(json_content, encoding="utf-8")
            
            print(f"[LLM_DOCS] Structure conversion documented: {input_path} -> {output_path}")
        except Exception as e:
            print(f"[LLM_DOCS] Could not document structure conversion: {e}")
        
        return structured_workout

    except Exception as e:
        print(f"Error in convert_freeform_to_schema: {e}")
        import traceback
        traceback.print_exc()
        raise

async def generate_workout(
    training_plan: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None
) -> str:
    """
    Generiert ein Workout mit LLM. Akzeptiert strukturierte Trainingsplandaten als String, 
    optionale Trainingshistorie als JSON-String und optionalen User Prompt.
    """
    try:
        # Load the Prompt File        
        prompt_path = Path(__file__).parent / PROMPT_FILE_FREEFORM
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()

        # Ensure default empty strings if None, to avoid issues with .format
        formatted_prompt = prompt_template_content.format(
            training_plan=training_plan if training_plan is not None else "",
            training_history=training_history if training_history is not None else "",
            user_prompt=user_prompt if user_prompt is not None else "",
            current_date=datetime.now().strftime("%d.%m.%Y"),
        )

        # API key aus der config holen
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2

        reasoning = {
            "effort": "low",
            "summary": None
        }
        
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY, use_responses_api=True, model_kwargs={"reasoning": reasoning})

        print("Sending request to OpenAI API (free-form)…")
        response = await llm.ainvoke(formatted_prompt)
        print("Received response from OpenAI API (free-form)")

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

        # ✅ Document freeform output
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            out_dir = Path(__file__).parent / "output"
            out_dir.mkdir(exist_ok=True)
            out_path = out_dir / f"{ts}_workout_generation_freeform_output.md"
            out_path.write_text(freeform_text, encoding="utf-8")
            print(f"[LLM_DOCS] Free-form output documented: {out_path}")
        except Exception as e:
            print(f"[LLM_DOCS] Could not document free-form output: {e}")

        return freeform_text

    except Exception as e:
        print(f"Error in generate_workout: {e}")
        import traceback
        traceback.print_exc()
        raise