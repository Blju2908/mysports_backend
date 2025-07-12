from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from app.llm.workout_generation.create_workout_schemas import WorkoutSchema
from app.core.config import get_config
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from sqlmodel.ext.asyncio.session import AsyncSession
from app.models.training_plan_model import TrainingPlan
from app.llm.workout_generation.exercise_filtering_service import (
    get_filtered_exercises_for_user,
    get_all_exercises_for_prompt,
)
import json

# Load prompt templates
def load_prompt_templates() -> Dict[str, Any]:
    """Load and return prompt templates and training principles."""
    
    # Load templates from files
    def _load_file(filename: str) -> str:
        path = Path(__file__).parent / "prompts" / filename
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    return {
        "freeform": PromptTemplate.from_template(
            _load_file("workout_generation_prompt_step1.md"), 
            template_format="f-string"
        ),
        "structure": PromptTemplate.from_template(
            _load_file("workout_generation_prompt_step2.md"),
            template_format="f-string"
        ),
        "training_principles": _load_file("training_principles_base.md"),
    }

# Create LCEL chains
def create_workout_generation_chains() -> Dict[str, Any]:
    """Create the LCEL chains for two-step workout generation using declarative pipes."""
    
    templates = load_prompt_templates()
    
    # Define LLMs for each step
    freeform_llm = get_llm_model(provider="openai", model="o4-mini")
    structure_llm = get_llm_model(provider="google", model="gemini-2.5-flash").with_structured_output(WorkoutSchema)

    # Helper Runnable for logging and passing data through
    def _log_and_pass_through(data: Dict[str, Any], stage: str, prompt_data_key: str, response_data_key: str) -> Dict[str, Any]:
        """Logs interaction and returns original data for the next step in the chain."""
        # Use the original input data for logging instead of the converted string
        prompt_data = data.get("original_input", data.get(prompt_data_key, "Prompt data not found"))
        response_data = data.get(response_data_key, "Response data not found")
        
        _document_llm_interaction(
            stage=stage,
            prompt=prompt_data,
            response=response_data,
        )

        # NEU: Konsolenausgabe für Freeform-Schritt
        if stage == "freeform_lcel":
            print("\n" + "="*70)
            print("                  📄 Freeform Workout Output (LCEL) 📄                  ")
            print("="*70)
            print(response_data)
            print("="*70 + "\n")

        return data

    # Define the full two-step generation process as a single, declarative chain
    full_chain = (
        RunnablePassthrough.assign(
            original_input=lambda x: x['input'],  # Store original input for logging
            freeform_text=(
                RunnableLambda(lambda x: x['input'])  # ✅ FIX: Unpack input for the prompt
                | templates["freeform"]
                | freeform_llm
                | StrOutputParser()
            )
        )
        | RunnableLambda(
            lambda data: _log_and_pass_through(data, "freeform_lcel", "input", "freeform_text")
        )
        | RunnablePassthrough.assign(
            structured_workout=(
                RunnableLambda(lambda x: {"FREEFORM_WORKOUT_PLACEHOLDER": x["freeform_text"]})
                | templates["structure"]
                | structure_llm
            )
        )
        | RunnableLambda(
            lambda data: _log_and_pass_through(data, "structure_lcel", "freeform_text", "structured_workout")
        )
        | RunnableLambda(lambda x: x["structured_workout"])  # Final step: extract the result
    )
    
    return {
        "full_chain": full_chain,
        "training_principles": templates["training_principles"]
    }

# Main execution function
async def execute_workout_generation_sequence(
    training_plan_obj: Optional[TrainingPlan] = None,
    training_plan_str: Optional[str] = None,
    training_history: Optional[str] = None,
    user_prompt: Optional[str] = None,
    db: Optional[AsyncSession] = None,
    use_exercise_filtering: bool = False,
    exercise_library: Optional[str] = None,
) -> WorkoutSchema:
    """
    Execute the two-step workout generation using a declarative LCEL chain.
    """
    _start_total = datetime.now()
    
    # Prepare exercise context
    if exercise_library is None:
        if use_exercise_filtering and training_plan_obj and db:
            try:
                print("🔍 Using DB Exercise Filtering...")
                exercise_library = await get_filtered_exercises_for_user(
                    training_plan=training_plan_obj, db=db, user_prompt=user_prompt
                )
                if exercise_library:
                    print(f"✅ Using {len(exercise_library.splitlines())} filtered exercises from DB")
                else:
                    print("⚠️ DB filtering failed, falling back to full DB list.")
            except Exception as e:
                print(f"Error in exercise filtering: {e}")
                exercise_library = None
        
        if exercise_library is None and db:
            exercise_library = await get_all_exercises_for_prompt(db)
    else:
        print(f"✅ Using pre-built exercise library ({len(exercise_library.splitlines())} exercises)")
    
    chains = create_workout_generation_chains()
    
    chain_inputs = {
        "training_plan": training_plan_str or "",
        "training_history": training_history or "",
        "user_prompt": user_prompt or "",
        "exercise_library": exercise_library or "",
        "training_principles": chains["training_principles"],
        "current_date": datetime.now().strftime("%d.%m.%Y"),
    }
    
    print("🔄 Executing declarative two-step workout generation chain...")
    # The 'input' key is added here to be explicitly available for logging
    structured_workout = await chains["full_chain"].ainvoke({"input": chain_inputs})
    
    _total_duration = (datetime.now() - _start_total).total_seconds()
    print(f"⏱️ TOTAL workout_generation duration: {_total_duration:.1f}s")
    
    return structured_workout


# Helper functions
def _document_llm_interaction(
    stage: str, prompt: Any, response: "str | WorkoutSchema", suffix: str = ""
) -> None:
    """Schreibt Prompt und Response formatiert mit Zeitstempel auf die Platte."""

    try:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        label = f"{stage}{'_' + suffix if suffix else ''}"
        out_dir = Path(__file__).parent / "output"
        out_dir.mkdir(exist_ok=True)

        # Bessere Prompt-Formatierung für Lesbarkeit
        prompt_path = out_dir / f"{ts}_{label}_prompt.md"
        
        prompt_content = f"# 🤖 Prompt für Stage: `{stage}`\n\n"
        prompt_content += f"**Timestamp:** {ts}\n\n"
        prompt_content += "---\n\n"

        if isinstance(prompt, dict):
            for key, value in prompt.items():
                # Create nice section headers
                section_title = key.replace('_', ' ').title()
                
                # Add emoji icons for better visual separation
                icons = {
                    'Training Plan': '📋',
                    'Training History': '📊', 
                    'User Prompt': '💬',
                    'Exercise Library': '🏋️',
                    'Training Principles': '📖',
                    'Current Date': '📅'
                }
                icon = icons.get(section_title, '📄')
                
                prompt_content += f"## {icon} {section_title}\n\n"
                
                # Handle different types of content
                if key == 'training_history' and isinstance(value, str) and value.strip().startswith('['):
                    # Format training history as readable JSON
                    try:
                        history_data = json.loads(value)
                        prompt_content += "```json\n"
                        prompt_content += json.dumps(history_data, indent=2, ensure_ascii=False)
                        prompt_content += "\n```\n\n"
                    except json.JSONDecodeError:
                        prompt_content += f"```\n{value}\n```\n\n"
                
                elif key == 'exercise_library':
                    # Format exercise library as a collapsible section
                    exercises = value.split('\n') if isinstance(value, str) else [str(value)]
                    exercise_count = len([e for e in exercises if e.strip() and not e.startswith('#')])
                    
                    prompt_content += f"**Anzahl verfügbare Übungen:** {exercise_count}\n\n"
                    prompt_content += "<details>\n<summary>📝 Vollständige Übungsliste (klicken zum Ausklappen)</summary>\n\n"
                    prompt_content += f"```\n{value}\n```\n\n"
                    prompt_content += "</details>\n\n"
                
                elif key == 'training_plan':
                    # Format training plan nicely
                    prompt_content += f"```markdown\n{value}\n```\n\n"
                
                elif key == 'training_principles':
                    # Format training principles
                    prompt_content += f"```markdown\n{value}\n```\n\n"
                
                else:
                    # Default formatting for other fields
                    if isinstance(value, str) and len(value) > 200:
                        prompt_content += f"```\n{value}\n```\n\n"
                    else:
                        prompt_content += f"**{value}**\n\n"
                
                prompt_content += "---\n\n"
        else:
            # Handle non-dict prompts
            prompt_content += f"```\n{str(prompt)}\n```\n\n"

        # Write the formatted prompt
        prompt_path.write_text(prompt_content, encoding="utf-8")

        # Response als JSON wenn möglich, sonst Markdown
        if hasattr(response, "model_dump_json"):
            output_text = response.model_dump_json(indent=2)
            output_path = out_dir / f"{ts}_{label}_response.json"
        else:
            output_text = str(response)
            output_path = out_dir / f"{ts}_{label}_response.md"

        output_path.write_text(output_text, encoding="utf-8")
        print(f"[LLM_DOCS] 📝 Documented {label}: {prompt_path.name} & {output_path.name}")
        
    except Exception as e:
        print(f"[LLM_DOCS] ❌ Could not document {stage}: {e}")


def get_llm_model(provider: str, model: str):
    """Get LLM model based on provider and model name."""
    if provider == "openai":
        if model == "o4-mini":
            reasoning = {
                "effort": "medium",
                "summary": None
            }
            return ChatOpenAI(
                model=model, 
                api_key=get_config().OPENAI_API_KEY2, 
                use_responses_api=True, 
                model_kwargs={"reasoning": reasoning}
            )
        else:
            return ChatOpenAI(model=model, api_key=get_config().OPENAI_API_KEY2)
    elif provider == "anthropic":
        return ChatAnthropic(model=model, api_key=get_config().ANTHROPIC_API_KEY)
    elif provider == "google":
        return ChatGoogleGenerativeAI(
            model=model, google_api_key=get_config().GOOGLE_API_KEY
        )
