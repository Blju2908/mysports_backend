from sqlmodel import SQLModel, Session, create_engine
from app.core.config import Settings

settings = Settings()

engine = create_engine(
    settings.SUPABASE_DB_URL,
)

def get_session() -> Session:
    with Session(engine) as session:
        yield session

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)