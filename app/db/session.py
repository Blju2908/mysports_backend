from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
import os
from sqlalchemy import text

logger = logging.getLogger(__name__)

# --- ✅ Auto-detect serverless environment ---
settings = get_config()

def is_serverless_environment():
    """Detect if running in serverless environment"""
    return (
        os.getenv("AWS_LAMBDA_FUNCTION_NAME") is not None or  # AWS Lambda
        os.getenv("VERCEL") is not None or  # Vercel
        os.getenv("RAILWAY_ENVIRONMENT") is not None or  # Railway
        os.path.exists("/var/task")  # AWS Lambda path
    )

# Configure based on environment
if is_serverless_environment():
    # SERVERLESS: Transaction Mode (Port 6543) + NullPool
    logger.info("🔄 Detected serverless environment - using Transaction Mode")
    
    # Ensure we have Transaction Mode URL (Port 6543)
    db_url = settings.SUPABASE_DB_URL
    if ":5432/" in db_url:
        db_url = db_url.replace(":5432/", ":6543/")
        logger.info("📝 Switched to Transaction Mode (Port 6543)")
    
    # Add pgbouncer parameter for prepared statements
    if "pgbouncer=true" not in db_url:
        separator = "&" if "?" in db_url else "?"
        db_url = f"{db_url}{separator}pgbouncer=true"
    
    engine = create_async_engine(
        db_url,
        echo=False,
        # NullPool für serverlose Umgebungen
        poolclass=NullPool,
        connect_args={
            "timeout": 10,  # Kurzer Timeout für serverless
            "command_timeout": 30,
            "server_settings": {
                "application_name": "s3ssions_api_serverless",
            },
        },
        execution_options={
            "isolation_level": "READ_COMMITTED"
        },
    )
    
else:
    # PERSISTENT: Session Mode (Port 5432) + AsyncAdaptedQueuePool
    logger.info("🏠 Detected persistent environment - using Session Mode")
    
    # Ensure we have Session Mode URL (Port 5432)
    db_url = settings.SUPABASE_DB_URL
    if ":6543/" in db_url:
        db_url = db_url.replace(":6543/", ":5432/")
        logger.info("📝 Switched to Session Mode (Port 5432)")
    
    engine = create_async_engine(
        db_url,
        echo=False,
        # AsyncAdaptedQueuePool für persistente Umgebungen
        poolclass=AsyncAdaptedQueuePool,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,
        connect_args={
            "timeout": 30,
            "command_timeout": 120,
            "server_settings": {
                "application_name": "s3ssions_api_persistent",
            },
        },
        execution_options={
            "isolation_level": "READ_COMMITTED"
        },
    )

# Create session maker
session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

logger.info("✅ SQLAlchemy engine configured successfully")
# --- End of AUTO-DETECTION ---


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

# Background task sessions
@asynccontextmanager
async def get_background_session():
    """Get database session for background tasks"""
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