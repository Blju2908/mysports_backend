# Standard workout generation chain
# This file defines the workflow for the standard workout generation

from .llm_call import create_workout_llm_call
from .service import create_workout_service

# The chain is implemented directly in the service for the standard version
# as it's a straightforward single LLM call without complex chaining