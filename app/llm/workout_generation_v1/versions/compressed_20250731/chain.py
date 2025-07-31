# Compressed workout generation chain with integrated LLM call
# Uses array-based format for ~90% token reduction

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from .schemas import CompactWorkoutSchema
import os


def create_compressed_workout_chain(api_key: str = None):
    """
    Creates a chain for compressed workout generation using array-based format.
    
    Args:
        api_key: Google API key for Gemini. If not provided, tries app config then environment variable.
        
    Returns:
        A LangChain chain that generates workouts in compressed format
    """
    # Get API key with multiple fallbacks
    if not api_key:
        # Try app config (for API usage)
        try:
            from app.core.config import get_config
            config = get_config()
            if hasattr(config, 'GOOGLE_API_KEY') and config.GOOGLE_API_KEY:
                api_key = config.GOOGLE_API_KEY
        except (ImportError, Exception):
            # Not in app context or config not available
            pass
    
    # Fallback to environment variable (for scripts)
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("Google API key must be provided as parameter, in app config, or set in GOOGLE_API_KEY environment variable")
    
    # Initialize LLM with Gemini 2.5 Flash
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        thinking_budget=512
    ).with_structured_output(CompactWorkoutSchema)    

    # Create prompt template (prompts will be loaded from files)
    prompt = ChatPromptTemplate.from_messages([
        ("system", "Du bist ein erfahrener Personal Trainer, der individuelle Workouts erstellt."),
        ("human", "{prompt}")
    ])
    
    # Create and return the chain
    chain = prompt | llm
    
    return chain


def invoke_compressed_workout_chain(chain, full_prompt: str) -> CompactWorkoutSchema:
    """
    Invokes the compressed workout chain with the given prompt.
    
    Args:
        chain: The LangChain chain
        full_prompt: The complete prompt including user context and format instructions
        
    Returns:
        CompactWorkoutSchema: The structured workout in compressed format
    """
    return chain.invoke({"prompt": full_prompt})