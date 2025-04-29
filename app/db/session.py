from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from typing import AsyncGenerator
from app.core.config import Settings

settings = Settings()

# Async Engine bauen
engine = create_async_engine(
    settings.SUPABASE_DB_URL,  # Achte darauf: Muss async-fähig sein, z.B. postgresql+asyncpg://
    echo=False,  # Optional: Logs zeigen
)

# Session Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        yield session
        
# Tabellen erzeugen
async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)