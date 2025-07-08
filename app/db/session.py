from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
# We rely on SQLAlchemy's built-in asyncpg pool. No separate asyncpg pool is
# created elsewhere, keeping a single pool strategy across the whole app.
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
import asyncio

logger = logging.getLogger(__name__)

# ✅ BEST PRACTICE: Simple SQLAlchemy engine for SQLModel compatibility
_engine = None
_session_maker = None

def get_engine():
    """Get or create SQLAlchemy engine"""
    global _engine, _session_maker
    if _engine is None:
        settings = get_config()
        
        # We let SQLAlchemy manage the connection pool (asyncpg based) itself. This
        # avoids maintaining a second pool (asyncpg) in `main.py` and follows the
        # single-pool best practice for Vercel deployments.

        _engine = create_async_engine(
            settings.SUPABASE_DB_URL,
            echo=False,
            pool_size=10,          # reasonable default; tune for Fluid Compute
            max_overflow=5,        # extra burst connections
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0,
                "command_timeout": 90,
                "server_settings": {
                    "application_name": "sqlalchemy_adapter"
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

# ✅ BEST PRACTICE: FastAPI dependency for API endpoints
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Get database session for API endpoints"""
    get_engine()  # Ensure engine is created
    
    async with _session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ BEST PRACTICE: Background task sessions
@asynccontextmanager
async def create_background_session():
    """Get database session for background tasks"""
    get_engine()  # Ensure engine is created
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with _session_maker() as session:
                try:
                    yield session
                    break
                except Exception as e:
                    logger.error(f"Background session error (attempt {attempt + 1}): {e}")
                    await session.rollback()
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))
                finally:
                    await session.close()
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Background session failed after {max_retries} attempts: {e}")
                raise
            await asyncio.sleep(1 * (attempt + 1))

# ✅ SIMPLE: Health check
async def test_db_connection():
    """Test database connection"""
    try:
        async with create_background_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            return row[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False

# ✅ SIMPLE: Retry helper
async def retry_db_operation(operation, max_retries=3, delay=1):
    """Retry database operations"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            logger.warning(f"DB operation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (attempt + 1))

# ✅ CLEANUP: Engine disposal
async def close_engine():
    """Close SQLAlchemy engine"""
    global _engine, _session_maker
    
    try:
        if _engine:
            await _engine.dispose()
            _engine = None
        _session_maker = None
        logger.info("✅ SQLAlchemy engine disposed")
    except Exception as e:
        logger.warning(f"Engine cleanup warning: {e}")