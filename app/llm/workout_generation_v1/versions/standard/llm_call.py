"""
Streamlined workout generation.

Workflow:
1.  Create a comprehensive prompt with general principles and user-specific data.
2.  Generate a freeform workout using a powerful language model.
3.  Structure the result into a clean JSON schema with a fast, specialized model.
"""

from langchain_google_genai import ChatGoogleGenerativeAI


def create_workout_with_llm(
    api_key: str,
    prompt: str,
):

    base_llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=api_key,
        thinking_budget=512
    )
    

    llm_output = base_llm.invoke(prompt)

    return llm_output
    
