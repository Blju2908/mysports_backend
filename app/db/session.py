from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)


settings = get_config()

# Single Engine - Supabase Session Mode für Vercel Pro + Background Tasks
db_url = settings.SUPABASE_DB_URL  # Port 5432 - Session Mode
logger.info("🚀 Unified Engine: Session Mode (Port 5432) - Vercel Pro + Background Tasks")

# Single Engine - Optimized for Supabase Session Mode + Vercel Pro
engine = create_async_engine(
    db_url,  # Session Mode URL (5432) - für alle Operations
    echo=False,
    poolclass=NullPool,      # ✅ Vercel Pro: Keine persistenten Connections zwischen Requests
    connect_args={
        "timeout": 20,                   # ✅ Längere Timeouts für Session Mode
        "command_timeout": 120,          # ✅ 2min für Background Tasks
        "server_settings": {
            "application_name": "s3ssions_unified_session",
        },
    },
    execution_options={
        "isolation_level": "READ_COMMITTED"
    },
)

# Single session maker - für alle Operations
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,        # ✅ Vercel Serverless: Manuelle Kontrolle
)

logger.info("✅ Unified Supabase engine configured:")
logger.info(f"   🚀 Single Engine: NullPool + Session Mode (5432) - Prepared statements enabled")
logger.info(f"   📊 Optimized for: API Endpoints + Background Tasks + Vercel Pro")
logger.info(f"   ⚡ Benefits: Better performance, longer timeouts, no pgbouncer restrictions")


def get_engine():
    return engine

# FastAPI dependency für API endpoints - Unified session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for API endpoints - Unified Supabase Session Mode"""
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"API session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            # ✅ Vercel Pro: Explicit cleanup
            await session.close()

# Background task sessions - Same unified session
@asynccontextmanager
async def get_background_session():
    """Get database session for background tasks - Same unified engine"""
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Background session error: {e}", exc_info=True)
            await session.rollback()
            raise
        finally:
            # ✅ Ensure cleanup
            await session.close()

# Engine cleanup
async def close_engine():
    """Close unified SQLAlchemy engine"""
    global engine, session_maker
    
    if engine:
        await engine.dispose()
        engine = None
        session_maker = None
        logger.info("✅ Unified SQLAlchemy engine disposed")