from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from app.core.config import Settings
import logging
import os
import asyncio

logger = logging.getLogger(__name__)

# ✅ VERCEL COMPATIBLE: Lazy-loaded engines (not global instances)
_engine: Optional = None
_session_maker: Optional = None

def get_engine():
    """✅ VERCEL COMPATIBLE: Lazy-loaded engine with minimal pooling"""
    global _engine
    if _engine is None:
        settings = Settings()
        
        # ✅ VERCEL OPTIMIZATION: Detect serverless environment
        is_serverless = os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME")
        
        if is_serverless:
            # 🔥 SERVERLESS: No pooling at all for maximum compatibility
            _engine = create_async_engine(
                settings.SUPABASE_DB_URL,
                pool_size=0,        # No pool
                max_overflow=0,     # No overflow
                pool_pre_ping=False, # No ping needed
                pool_recycle=-1,    # No recycle
                echo=False,         # No echo in production
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                    "server_settings": {
                        "application_name": "vercel_serverless"
                    }
                }
            )
            logger.info("✅ Serverless database engine created (No pooling)")
        else:
            # 🔧 LOCAL: Minimal pooling for development
            _engine = create_async_engine(
                settings.SUPABASE_DB_URL,
                pool_size=1,        # Minimal pool for local
                max_overflow=2,     # Small overflow
                pool_pre_ping=True,
                pool_recycle=300,
                echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
                connect_args={
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0,
                    "server_settings": {
                        "application_name": "local_development"
                    }
                }
            )
            logger.info("✅ Local database engine created (Minimal pooling)")
    
    return _engine

def get_session_maker():
    """✅ VERCEL COMPATIBLE: Lazy-loaded session maker"""
    global _session_maker
    if _session_maker is None:
        _session_maker = async_sessionmaker(
            get_engine(), 
            class_=AsyncSession, 
            expire_on_commit=False,
            autoflush=False
        )
        logger.info("✅ Session maker created (Vercel compatible)")
    return _session_maker

# ✅ VERCEL COMPATIBLE: FastAPI Dependency with lazy loading
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Vercel compatible session dependency with lazy loading"""
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ VERCEL COMPATIBLE: Background Tasks with single connection
@asynccontextmanager
async def create_background_session():
    """
    ✅ VERCEL OPTIMIZED: Single connection for background tasks
    Creates a fresh engine per background task to avoid pooling issues
    """
    settings = Settings()
    
    # 🔥 BACKGROUND TASKS: Fresh engine per task (no pooling)
    temp_engine = create_async_engine(
        settings.SUPABASE_DB_URL,
        pool_size=0,         # No pool
        max_overflow=0,      # No overflow  
        pool_pre_ping=False, # No ping
        pool_recycle=-1,     # No recycle
        echo=False,          # No echo
        connect_args={
            "statement_cache_size": 0,
            "prepared_statement_cache_size": 0,
            "server_settings": {
                "application_name": "background_task"
            }
        }
    )
    
    temp_session_maker = async_sessionmaker(
        temp_engine, 
        class_=AsyncSession, 
        expire_on_commit=False,
        autoflush=False
    )
    
    logger.info("✅ Background session engine created (Single connection)")
    
    session = None
    try:
        session = temp_session_maker()
        yield session
    except Exception as e:
        logger.error(f"Background session error: {e}")
        if session:
            await session.rollback()
        raise
    finally:
        if session:
            await session.close()
        # 🔥 CRITICAL: Dispose engine after use
        await temp_engine.dispose()
        logger.info("✅ Background session disposed")

# ✅ VERCEL COMPATIBLE: Optional table creation (only for development)
async def create_db_and_tables():
    """Create database tables - Vercel compatible"""
    engine = get_engine()
    try:
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("✅ Database tables created (Vercel compatible)")
    except Exception as e:
        logger.error(f"Table creation error: {e}")
        # Don't fail in production
        if not os.getenv("VERCEL"):
            raise

# ✅ VERCEL COMPATIBLE: Optional cleanup (may not be called in serverless)
async def close_engine():
    """Close database engines - may not be called in Vercel"""
    global _engine, _session_maker
    
    try:
        if _engine:
            await _engine.dispose()
            _engine = None
        
        _session_maker = None
        
        logger.info("✅ Database engines disposed (Vercel compatible)")
    except Exception as e:
        logger.warning(f"Engine cleanup warning (normal in serverless): {e}")

# ✅ VERCEL HELPER: Connection retry for robustness
async def retry_db_operation(operation, max_retries=3, delay=1):
    """Helper for retrying database operations in serverless environments"""
    for attempt in range(max_retries):
        try:
            return await operation()
        except Exception as e:
            logger.warning(f"DB operation attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (attempt + 1))  # Exponential backoff