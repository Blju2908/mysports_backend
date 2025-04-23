from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_PORT: int
    MAIL_SERVER: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool

    # Supabase
    SUPABASE_URL: str
    SUPABASE_API_KEY: str
    SUPABASE_DB_URL: str
    SUPABASE_BUCKET: str

    class Config:
        env_file = ".env"
        case_sensitive = True 