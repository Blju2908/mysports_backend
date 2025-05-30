from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from typing import Optional
from datetime import datetime
from pathlib import Path
from app.core.config import get_config
import os

# Constants
PROMPT_FILE = "workout_generation_prompt_text_schema.md"

async def generate_workout_reasoning_only(
    training_plan: str | None = None,
    training_history: str | None = None,
    user_prompt: str | None = None,
) -> str:
    """
    Generiert ein Workout mit LLM im Reasoning-Schritt (Text Output).
    Nutzt LangChain Best Practices mit PromptTemplate und Chain Composition.
    
    Args:
        training_plan: Trainingsprinzipien als String
        training_history: Trainingshistorie als JSON-String 
        user_prompt: Optionaler User Prompt
        
    Returns:
        str: Workout als formatierter Text (nicht JSON)
    """
    try:
        # Load prompt template from file
        prompt_path = Path(__file__).parent / PROMPT_FILE
        with open(prompt_path, "r", encoding="utf-8") as f:
            prompt_template_content = f.read()
        
        # Create LangChain PromptTemplate
        reasoning_prompt = PromptTemplate(
            input_variables=["training_plan", "training_history", "user_prompt", "current_date"],
            template=prompt_template_content
        )
        
        # Prepare input data
        input_data = {
            "training_plan": training_plan or "",
            "training_history": training_history or "",
            "user_prompt": user_prompt or "",
            "current_date": datetime.now().strftime("%d.%m.%Y")
        }
        
        # API key from config
        config = get_config()
        OPENAI_API_KEY = config.OPENAI_API_KEY2
        
        # Configure LLM for reasoning
        reasoning = {
            "effort": "low",
            "summary": None
        }
        
        llm = ChatOpenAI(
            model="o4-mini", 
            api_key=OPENAI_API_KEY, 
            use_responses_api=True, 
            model_kwargs={"reasoning": reasoning}
        )
        
        # Build LangChain chain with simple composition
        chain = reasoning_prompt | llm | StrOutputParser()
        
        # Document input if enabled
        should_document_input = True
        if should_document_input:
            await document_reasoning_input(input_data)
        
        print("Sending reasoning request to OpenAI API...")
        reasoning_output = await chain.ainvoke(input_data)
        print("Received reasoning response from OpenAI API")
        
        # Document output if enabled
        should_document_output = True
        if should_document_output:
            await document_reasoning_output(reasoning_output)
        
        return reasoning_output
        
    except Exception as e:
        print(f"Error generating workout: {e}")
        import traceback
        traceback.print_exc()
        raise e

async def document_reasoning_input(input_data: dict) -> None:
    """
    Document the input of the reasoning chain.
    """
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "output")
        
        # Check if folder "output" exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Create a file with the current date
        file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_reasoning_input.md"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Reasoning Chain Input\n\n")
            f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("## Training Plan\n")
            f.write(f"```\n{input_data.get('training_plan', 'None')}\n```\n\n")
            
            f.write("## Training History\n")
            f.write(f"```json\n{input_data.get('training_history', 'None')}\n```\n\n")
            
            f.write("## User Prompt\n")
            f.write(f"```\n{input_data.get('user_prompt', 'None')}\n```\n\n")
            
            f.write("## Current Date\n")
            f.write(f"```\n{input_data.get('current_date', 'None')}\n```\n")
            
    except Exception as e:
        print(f"Error in document_reasoning_input: {e}")

async def document_reasoning_output(reasoning_output: str) -> None:
    """
    Document the output of the reasoning chain.
    """
    try:
        # Get the directory of the current file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        output_dir = os.path.join(current_dir, "output")
        
        # Check if folder "output" exists, if not create it
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Create a file with the current date
        file_name = f"{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}_reasoning_output.md"
        file_path = os.path.join(output_dir, file_name)
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write("# Reasoning Chain Output\n\n")
            f.write(f"**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write("## Generated Workout (Text Format)\n\n")
            f.write(reasoning_output)
            
    except Exception as e:
        print(f"Error in document_reasoning_output: {e}")
