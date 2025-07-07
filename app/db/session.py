from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import Settings
import logging

logger = logging.getLogger(__name__)

# ✅ STANDARD: Global Engine (FastAPI Best Practice)
settings = Settings()
engine = create_async_engine(
    settings.SUPABASE_DB_URL,
    # ✅ PRAGMATIC: Moderate Connection Pool für Supabase
    pool_size=5,        # Reduced from 20
    max_overflow=10,    # Reduced from 30 (= 15 connections per worker)
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)

# ✅ STANDARD: Session Factory
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

logger.info("✅ Database engine initialized (Standard FastAPI Pattern)")

# ✅ STANDARD: FastAPI Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Standard FastAPI session dependency"""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ BACKGROUND TASKS: Separate Engine for Background Tasks
background_engine = create_async_engine(
    settings.SUPABASE_DB_URL,
    # ✅ SEPARATE: Independent connection pool for background tasks
    pool_size=3,        # Smaller pool for background tasks
    max_overflow=5,     # = 8 connections per worker for background tasks
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
    connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    }
)

# ✅ BACKGROUND TASKS: Separate Session Factory
background_session_maker = async_sessionmaker(
    background_engine, 
    class_=AsyncSession, 
    expire_on_commit=False,
    autoflush=False
)

logger.info("✅ Background database engine initialized")

# ✅ BACKGROUND TASKS: Dedicated Context Manager
@asynccontextmanager
async def create_background_session():
    """Context manager for background tasks with separate engine"""
    async with background_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Background session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ STANDARD: Database Tables Creation (für Development)
async def create_db_and_tables():
    """Create database tables - only for development"""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("✅ Database tables created")

# ✅ STANDARD: Engine Cleanup
async def close_engine():
    """Close database engines - for app shutdown"""
    await engine.dispose()
    await background_engine.dispose()
    logger.info("✅ Database engines disposed")