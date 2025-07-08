from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging

logger = logging.getLogger(__name__)

# Global engine and session maker
_engine = None
_session_maker = None

def get_engine():
    """Get or create SQLAlchemy engine"""
    global _engine, _session_maker
    if _engine is None:
        settings = get_config()
        
        _engine = create_async_engine(
            settings.SUPABASE_DB_URL,
            echo=False,
            pool_size=10,
            max_overflow=5,
            # ✅ Supabase/PgBouncer compatibility
            pool_pre_ping=True,
            pool_recycle=3600,  # 1 hour
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "command_timeout": 120,
                "server_settings": {
                    "application_name": "s3ssions_api"
                }
            }
        )
        
        _session_maker = async_sessionmaker(
            bind=_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("✅ SQLAlchemy engine created")
    
    return _engine

# FastAPI dependency for API endpoints
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for API endpoints"""
    get_engine()
    
    async with _session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"API session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Background task sessions - isolated and robust
@asynccontextmanager
async def get_background_session():
    """Get isolated database session for background tasks"""
    get_engine()
    
    async with _session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Background session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# Engine cleanup
async def close_engine():
    """Close SQLAlchemy engine"""
    global _engine, _session_maker
    
    if _engine:
        await _engine.dispose()
        _engine = None
        _session_maker = None
        logger.info("✅ SQLAlchemy engine disposed")