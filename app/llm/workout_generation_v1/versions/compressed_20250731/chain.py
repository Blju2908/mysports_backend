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
        api_key: Google API key for Gemini. If not provided, uses environment variable.
        
    Returns:
        A LangChain chain that generates workouts in compressed format
    """
    # Get API key
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
    
    if not api_key:
        raise ValueError("Google API key must be provided or set in GOOGLE_API_KEY environment variable")
    
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