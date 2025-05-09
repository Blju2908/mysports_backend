from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from app.llm.schemas.training_principle_schemas import TrainingPrinciplesResponseSchema
from app.llm.utils.langchain_utils import load_prompt
from app.core.config import get_config
from datetime import datetime
import json

PROMPT_FILE = "training_principles_prompt.md"

async def generate_training_principles(training_goals: dict | None = None):
    """
    Leitet aus den Trainingszielen professionelle Trainingsprinzipien ab.
    """
    try:
        training_goals_json = json.dumps(training_goals, ensure_ascii=False, indent=2) if training_goals else None
        prompt_template = load_prompt(PROMPT_FILE)
        prompt = prompt_template.format(
            training_goals=training_goals_json or "{}",
        )

        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        llm = ChatOpenAI(model="o4-mini", api_key=OPENAI_API_KEY)

        chain = ChatPromptTemplate.from_template(
            "{prompt}"
        ) | llm.with_structured_output(TrainingPrinciplesResponseSchema)
        print("Sending request to OpenAI API for training principles...")
        result = await chain.ainvoke({"prompt": prompt})
        print("Received response from OpenAI API")
        return result
    except Exception as e:
        print(f"Error in generate_training_principles: {e}")
        import traceback
        traceback.print_exc()
        raise 