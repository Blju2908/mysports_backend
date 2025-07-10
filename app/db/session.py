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

# --- ✅ SIMPLE: Always Session Mode (Port 5432) with 2 separate pools ---
settings = get_config()

# Ensure we use Session Mode (Port 5432)
api_db_url = settings.SUPABASE_DB_URL
if ":6543/" in api_db_url:
    api_db_url = api_db_url.replace(":6543/", ":5432/")
    logger.info("📝 Switched from Transaction Mode to Session Mode (Port 5432)")

logger.info("🎯 Using Session Mode (Port 5432) for ALL connections")

# API Engine - Small pool for fast API requests
engine = create_async_engine(
    api_db_url,
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,           # API Pool: 5 connections
    max_overflow=5,        # Can grow to 10 total
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=3600,     # Recycle after 1 hour
    connect_args={
        "timeout": 30,               # 30s connection timeout
        "command_timeout": 120,      # 2 minutes for API queries
        "server_settings": {
            "application_name": "s3ssions_api",
        },
    },
    execution_options={
        "isolation_level": "READ_COMMITTED"
    },
)

# Background Engine - Separate pool for long-running tasks
background_engine = create_async_engine(
    api_db_url,  # Same URL, different pool
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=3,           # Background Pool: 3 connections 
    max_overflow=2,        # Can grow to 5 total
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=1800,     # Recycle after 30 minutes (more frequent)
    connect_args={
        "timeout": 30,               # 30s connection timeout
        "command_timeout": 600,      # 10 minutes for LLM calls
        "server_settings": {
            "application_name": "s3ssions_background",
        },
    },
    execution_options={
        "isolation_level": "READ_COMMITTED"
    },
)

# Create session makers
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

background_session_maker = async_sessionmaker(
    bind=background_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

logger.info("✅ Session Mode engines configured:")
logger.info(f"   🔹 API Pool: {engine.pool.size()} connections + {engine.pool._max_overflow} overflow")
logger.info(f"   🔹 Background Pool: {background_engine.pool.size()} connections + {background_engine.pool._max_overflow} overflow")


def get_engine():
    """Returns the API SQLAlchemy engine."""
    return engine

def get_background_engine():
    """Returns the Background Tasks SQLAlchemy engine."""
    return background_engine

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

# Background task sessions - SEPARATE ENGINE & POOL!
@asynccontextmanager
async def get_background_session():
    """Get database session for background tasks - uses separate engine & pool!"""
    async with background_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Background session error: {e}", exc_info=True)
            await session.rollback()
            raise

# Engine cleanup
async def close_engine():
    """Close SQLAlchemy engines"""
    global engine, background_engine, session_maker, background_session_maker
    
    if engine:
        await engine.dispose()
        engine = None
        session_maker = None
        logger.info("✅ API SQLAlchemy engine disposed")
        
    if background_engine:
        await background_engine.dispose()
        background_engine = None
        background_session_maker = None
        logger.info("✅ Background SQLAlchemy engine disposed")