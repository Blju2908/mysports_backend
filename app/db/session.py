from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
from app.core.config import Settings
from sqlalchemy.pool import NullPool



def get_engine():
    settings = Settings()
    return create_async_engine(
        settings.SUPABASE_DB_URL,  # Achte darauf: Muss async-fähig sein, z.B. postgresql+asyncpg://
        poolclass=NullPool,
        connect_args={
            "statement_cache_size": 0,              # Deaktiviert statement caching
            "prepared_statement_cache_size": 0      # Für asyncpg spezifisch
        }
    )

# Session Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    engine = get_engine()
    async with AsyncSession(engine) as session:
        yield session
        
# Tabellen erzeugen
async def create_db_and_tables():
    async with get_engine().begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)