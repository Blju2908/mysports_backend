from supabase import create_client, Client
from app.core.config import Settings
from functools import lru_cache

settings = Settings()

@lru_cache()
def get_supabase_client() -> Client:
    """
    Creates and returns a Supabase client instance with caching
    """
    return create_client(
        supabase_url=settings.SUPABASE_URL,
        supabase_key=settings.SUPABASE_API_KEY
    ) 