from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

# --- ✅ DUAL-MODE: Transaction Mode for API + Session Mode for Background ---
settings = get_config()

# API Engine - Transaction Mode (6543) für AWS Lambda Serverless
api_db_url = settings.SUPABASE_DB_URL_TRANSACTION
logger.info("🚀 API Engine: Transaction Mode (Port 6543) - Optimized for Serverless")

# Background Engine - Session Mode (5432) für DB-intensive Operations
bg_db_url = settings.SUPABASE_DB_URL
if ":6543/" in bg_db_url:
    bg_db_url = bg_db_url.replace(":6543/", ":5432/")
logger.info("🗄️  Background Engine: Session Mode (Port 5432) - Optimized for DB Operations")

# API Engine - Transaction Mode für schnelle Serverless Responses
engine = create_async_engine(
    api_db_url,  # Transaction Mode URL (6543)
    echo=False,
    poolclass=NullPool,      # ✅ Serverless: Keine persistenten Connections
    connect_args={
        "timeout": 5,                    # ✅ Schneller Timeout für Lambda
        "command_timeout": 30,           # ✅ Kurze API-Queries
        "statement_cache_size": 0,       # ✅ Disable prepared statements for pgbouncer transaction mode
        "server_settings": {
            "application_name": "s3ssions_api_transaction",
        },
    },
    execution_options={
        "isolation_level": "READ_COMMITTED"
    },
)

# Background Engine - Session Mode für DB-intensive Operations
background_engine = create_async_engine(
    bg_db_url,   # Session Mode URL (5432)
    echo=False,
    poolclass=AsyncAdaptedQueuePool,
    pool_size=5,           # Background Pool: 5 connections 
    max_overflow=3,        # Can grow to 8 total
    pool_pre_ping=True,    # Test connections before use
    pool_recycle=1800,     # Recycle after 30 minutes
    connect_args={
        "timeout": 15,               # ✅ Moderate timeout für Session Mode
        "command_timeout": 300,      # ✅ 5 min für DB-Operations (LLM-Calls sind separat)
        "server_settings": {
            "application_name": "s3ssions_background_session",
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

logger.info("✅ Dual-Mode engines configured:")
logger.info(f"   🚀 API Engine (Transaction Mode): NullPool - Serverless optimized")
logger.info(f"   🗄️  Background Engine (Session Mode): {background_engine.pool.size()} connections + {background_engine.pool._max_overflow} overflow")


def get_engine():
    """Returns the API SQLAlchemy engine (Transaction Mode)."""
    return engine

def get_background_engine():
    """Returns the Background Tasks SQLAlchemy engine (Session Mode)."""
    return background_engine

# FastAPI dependency for API endpoints - Transaction Mode
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for API endpoints (Transaction Mode 6543)"""
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"API session error (Transaction Mode): {e}", exc_info=True)
            await session.rollback()
            raise

# Background task sessions - Session Mode für DB-Operations
@asynccontextmanager
async def get_background_session():
    """Get database session for background tasks (Session Mode 5432) - SHORT DB operations only!"""
    async with background_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            logger.error(f"Background session error (Session Mode): {e}", exc_info=True)
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
        logger.info("✅ API SQLAlchemy engine disposed (Transaction Mode)")
        
    if background_engine:
        await background_engine.dispose()
        background_engine = None
        background_session_maker = None
        logger.info("✅ Background SQLAlchemy engine disposed (Session Mode)")