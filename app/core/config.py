from pydantic_settings import BaseSettings
import os

# Determine environment
def get_environment():
    return os.getenv("APP_ENV", "development")

class Settings(BaseSettings):
    OPENAI_API_KEY2: str
    
    # Supabase
    SUPABASE_URL: str
    SUPABASE_API_KEY: str  # This should be the anon key (public, for client-side usage)
    SUPABASE_DB_URL: str
    SUPABASE_SERVICE_ROLE_KEY: str  # This should be the service role key (private, for backend/admin usage)
    ALEMBIC_DB_URL: str
    
    # Email settings
    MAIL_USERNAME: str = os.getenv("MAIL_USERNAME", "")
    MAIL_PASSWORD: str = os.getenv("MAIL_PASSWORD", "")
    MAIL_FROM: str = os.getenv("MAIL_FROM", "noreply@mysports.com")
    MAIL_PORT: int = int(os.getenv("MAIL_PORT", "587"))
    MAIL_SERVER: str = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    MAIL_FROM_NAME: str = os.getenv("MAIL_FROM_NAME", "MySports")
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True
    MAIL_USE_CREDENTIALS: bool = True
    MAIL_VALIDATE_CERTS: bool = True

    class Config:
        env_file = f".env.{get_environment()}"
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