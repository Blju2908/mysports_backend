from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY2: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_API_KEY: str
    SUPABASE_DB_URL: str
    SUPABASE_BUCKET: str
    ALEMBIC_DB_URL: str

    class Config:
        env_file = ".env"
        case_sensitive = True 

# Create a singleton instance
_settings = None

def get_config() -> Settings:
    """
    Returns a singleton instance of the Settings class.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings 