from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine, async_sessionmaker
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from app.core.config import Settings
from sqlalchemy.pool import AsyncAdaptedQueuePool
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Singleton für Engine und Session Management"""
    _engine: Optional[AsyncEngine] = None
    _session_factory: Optional[async_sessionmaker] = None
    
    @classmethod
    def get_engine(cls) -> AsyncEngine:
        """Gibt die Singleton Engine zurück"""
        if cls._engine is None:
            settings = Settings()
            cls._engine = create_async_engine(
                settings.SUPABASE_DB_URL,
                # ✅ VERBESSERT: AsyncAdaptedQueuePool für async engines
                poolclass=AsyncAdaptedQueuePool,
                pool_size=20,
                max_overflow=30,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0
                }
            )
            logger.info("✅ Database engine initialized (Singleton)")
        return cls._engine
    
    @classmethod
    def get_session_factory(cls):
        """Gibt die Singleton Session Factory zurück"""
        if cls._session_factory is None:
            cls._session_factory = async_sessionmaker(
                cls.get_engine(),
                expire_on_commit=False,
                autoflush=False,
                class_=AsyncSession,
            )
            logger.info("✅ Session factory initialized (Singleton)")
        return cls._session_factory
    
    @classmethod
    async def close_engine(cls):
        """Schließt die Engine (für App-Shutdown)"""
        if cls._engine:
            await cls._engine.dispose()
            cls._engine = None
            cls._session_factory = None
            logger.info("✅ Database engine closed")

# Session Dependency für FastAPI
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI Dependency für Request-Sessions"""
    session_factory = DatabaseManager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise

# Background Task Context Manager
@asynccontextmanager
async def create_background_session():
    """
    Context manager für Background Tasks
    Nutzt die Singleton Engine/Session Factory
    """
    session_factory = DatabaseManager.get_session_factory()
    async with session_factory() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Background session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Database Tables erstellen
async def create_db_and_tables():
    """Erstellt Database Tables"""
    engine = DatabaseManager.get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)