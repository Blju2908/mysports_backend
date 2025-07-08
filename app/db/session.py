from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from app.core.config import get_config
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# ✅ SUPABASE TRANSACTION MODE: Lazy-loaded engines
_engine: Optional = None
_session_maker: Optional = None

def get_engine():
    """✅ SUPABASE TRANSACTION MODE: Engine optimized for 6543 pooler with full AsyncPG config"""
    global _engine
    if _engine is None:
        settings = get_config()
        
        # ✅ VERCEL OPTIMIZATION: Detect serverless environment
        is_serverless = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        
        # 🔥 CRITICAL: Complete AsyncPG configuration for Transaction Mode
        asyncpg_config = {
            # Required for Transaction Mode (per Supabase docs)
            "statement_cache_size": 0,              # Disable statement cache
            "prepared_statement_cache_size": 0,     # Disable prepared statement cache
            "command_timeout": 90,                  # 90 seconds timeout for long-running operations
            "server_settings": {
                "application_name": "vercel_serverless_tx" if is_serverless else "local_dev_tx"
            }
        }
        
        if is_serverless:
            # 🔥 SERVERLESS + TRANSACTION MODE: NullPool for maximum compatibility
            _engine = create_async_engine(
                settings.SUPABASE_DB_URL,  # Now using 6543 (Transaction Mode)
                poolclass=NullPool,         # No pooling at all
                echo=False,                 # No echo in production
                connect_args=asyncpg_config
            )
            logger.info("✅ Serverless Transaction Mode engine created (NullPool + 90s timeout)")
        else:
            # 🔧 LOCAL + TRANSACTION MODE: Minimal pooling for development
            _engine = create_async_engine(
                settings.SUPABASE_DB_URL,  # Now using 6543 (Transaction Mode)
                pool_size=2,                # Small pool for local development
                max_overflow=1,             # Small overflow
                pool_pre_ping=True,         # Ping for health checks
                pool_recycle=300,           # 5 minutes recycle
                echo=False,                 # Set to True for SQL debugging
                connect_args=asyncpg_config
            )
            logger.info("✅ Local Transaction Mode engine created (Small pool + 90s timeout)")
    
    return _engine

def get_session_maker():
    """✅ SUPABASE TRANSACTION MODE: Lazy-loaded session maker"""
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(), 
            class_=AsyncSession, 
            expire_on_commit=False,
            autoflush=False,
            autocommit=False
        )
        logger.info("✅ Transaction Mode session maker created")
    return _session_maker

# ✅ SUPABASE TRANSACTION MODE: FastAPI Dependency
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Transaction Mode compatible session dependency"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ SUPABASE TRANSACTION MODE: Background Tasks with retry logic
@asynccontextmanager
async def create_background_session():
    """
    ✅ SUPABASE TRANSACTION MODE: Optimized for background tasks with retry
    Uses the same engine but with fresh session per task
    """
    session_maker = get_session_maker()
    
    logger.info("✅ Background session created (Transaction Mode)")
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            async with session_maker() as session:
                try:
                    yield session
                    break  # Success, exit retry loop
                except Exception as e:
                    logger.error(f"Background session error (attempt {attempt + 1}): {e}")
                    await session.rollback()
                    if attempt == max_retries - 1:
                        raise
                    await asyncio.sleep(1 * (attempt + 1))  # Exponential backoff
                finally:
                    await session.close()
                    logger.info("✅ Background session closed")
        except Exception as e:
            if attempt == max_retries - 1:
                logger.error(f"Background session failed after {max_retries} attempts: {e}")
                raise
            await asyncio.sleep(1 * (attempt + 1))

# ✅ SUPABASE TRANSACTION MODE: Optional table creation
async def create_db_and_tables():
    """Create database tables - Transaction Mode compatible"""
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Database tables created (Transaction Mode)")
    except Exception as e:
        logger.error(f"Table creation error: {e}")
        # Don't fail in production
        if not os.getenv("VERCEL"):
            raise

# ✅ SUPABASE TRANSACTION MODE: Cleanup
async def close_engine():
    """Close database engines - Transaction Mode compatible"""
    global _engine, _session_maker
    
    try:
        if _engine:
            await _engine.dispose()
            _engine = None
        
        _session_maker = None
        
        logger.info("✅ Transaction Mode engines disposed")
    except Exception as e:
        logger.warning(f"Engine cleanup warning (normal in serverless): {e}")

# ✅ SUPABASE TRANSACTION MODE: Connection retry helper
async def retry_db_operation(operation, max_retries=3, delay=1):
    """Helper for retrying database operations in Transaction Mode"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            logger.warning(f"DB operation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff

# ✅ SUPABASE TRANSACTION MODE: Health check helper
async def test_db_connection():
    """Test database connection for health checks"""
    try:
        async with create_background_session() as session:
            from sqlalchemy import text
            result = await session.execute(text("SELECT 1"))
            row = result.fetchone()
            return row[0] == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False