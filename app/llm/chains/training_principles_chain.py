from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.utils.langchain_utils import load_prompt
from app.core.config import get_config
from datetime import date
import json

PROMPT_FILE = "training_principles_prompt.md"

async def generate_training_principles(training_goals: dict | None = None) -> str:
    """
    Leitet aus den Trainingszielen professionelle Trainingsprinzipien als Fließtext ab.
    Spricht den Nutzer direkt an und berücksichtigt das aktuelle Datum.
    """
    try:
        training_goals_json = json.dumps(training_goals, ensure_ascii=False, indent=2, default=str) if training_goals else None
        current_date_iso = date.today().isoformat()
        
        prompt_template = load_prompt(PROMPT_FILE)
        prompt = prompt_template.format(
            training_goals=training_goals_json or "{}",
            current_date=current_date_iso
        )

        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)

        chain = ChatPromptTemplate.from_template(
            "{prompt}"
        ) | llm 
        
        print("Sending request to OpenAI API for training principles (text output, direct address, with current date)...")
        ai_message_result = await chain.ainvoke({"prompt": prompt})
        result_text = ai_message_result.content 
        print("Received response from OpenAI API (text output)")
        return result_text
    except Exception as e:
        print(f"Error in generate_training_principles: {e}")
        import traceback
        traceback.print_exc()
        raise 