from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# --- ✅ NEW: Module-level initialization for Session Mode (Port 5432) ---
settings = get_config()

# Create engine for Session Mode - much simpler configuration
engine = create_async_engine(
    settings.SUPABASE_DB_URL,
    echo=False,
    # AsyncAdaptedQueuePool für Session Mode mit AsyncIO - unterstützt prepared statements vollständig
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,  # Recycle connections every hour
    connect_args={
        "timeout": 30,
        "command_timeout": 120,
        "server_settings": {
            "application_name": "s3ssions_api",
        },
    },
    # Session Mode: Keine speziellen execution_options nötig
    execution_options={
        "isolation_level": "READ_COMMITTED"
    },
)

# Create session maker directly
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

logger.info("✅ SQLAlchemy engine configured for Session Mode (Port 5432)")
# --- End of NEW ---


def get_engine():
    """Returns the globally available SQLAlchemy engine."""
    return engine

# FastAPI dependency for API endpoints
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for API endpoints"""
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"API session error: {e}", exc_info=True)
            await session.rollback()
            raise

# Background task sessions - now much simpler thanks to Session Mode
@asynccontextmanager
async def get_background_session():
    """Get database session for background tasks - Session Mode supports all features"""
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Background session error: {e}", exc_info=True)
            await session.rollback()
            raise

# Engine cleanup
async def close_engine():
    """Close SQLAlchemy engine"""
    global engine, session_maker
    
    if engine:
        await engine.dispose()
        engine = None
        session_maker = None
        logger.info("✅ SQLAlchemy engine disposed")