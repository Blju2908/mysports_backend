from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator, Optional
from contextlib import asynccontextmanager
from app.core.config import Settings
import logging
import os

logger = logging.getLogger(__name__)

# ✅ VERCEL COMPATIBLE: Lazy-loaded engines (not global instances)
_engine: Optional = None
_background_engine: Optional = None
_session_maker: Optional = None
_background_session_maker: Optional = None

def get_engine():
    """✅ VERCEL COMPATIBLE: Lazy-loaded engine creation"""
    global _engine
    if _engine is None:
        settings = Settings()
        _engine = create_async_engine(
            settings.SUPABASE_DB_URL,
            # ✅ VERCEL: Smaller pools for serverless
            pool_size=1,        # Minimal pool for serverless
            max_overflow=2,     # Small overflow
            pool_pre_ping=True,
            pool_recycle=300,   # Shorter recycle for serverless
            echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0
            }
        )
        logger.info("✅ Database engine created (Vercel compatible)")
    return _engine

def get_background_engine():
    """✅ VERCEL COMPATIBLE: Lazy-loaded background engine"""
    global _background_engine
    if _background_engine is None:
        settings = Settings()
        _background_engine = create_async_engine(
            settings.SUPABASE_DB_URL,
            # ✅ VERCEL: Minimal pool for background tasks
            pool_size=1,
            max_overflow=1,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=settings.DEBUG if hasattr(settings, 'DEBUG') else False,
            connect_args={
                "statement_cache_size": 0,
                "prepared_statement_cache_size": 0
            }
        )
        logger.info("✅ Background database engine created (Vercel compatible)")
    return _background_engine

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

def get_background_session_maker():
    """✅ VERCEL COMPATIBLE: Lazy-loaded background session maker"""
    global _background_session_maker
    if _background_session_maker is None:
        _background_session_maker = async_sessionmaker(
            get_background_engine(), 
            class_=AsyncSession, 
            expire_on_commit=False,
            autoflush=False
        )
        logger.info("✅ Background session maker created (Vercel compatible)")
    return _background_session_maker

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

# ✅ VERCEL COMPATIBLE: Background Tasks with lazy loading
@asynccontextmanager
async def create_background_session():
    """Vercel compatible background session with lazy loading"""
    background_session_maker = get_background_session_maker()
    async with background_session_maker() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Background session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()

# ✅ VERCEL COMPATIBLE: Optional table creation (only for development)
async def create_db_and_tables():
    """Create database tables - Vercel compatible"""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logger.info("✅ Database tables created (Vercel compatible)")

# ✅ VERCEL COMPATIBLE: Optional cleanup (may not be called in serverless)
async def close_engine():
    """Close database engines - may not be called in Vercel"""
    global _engine, _background_engine, _session_maker, _background_session_maker
    
    try:
        if _engine:
            await _engine.dispose()
            _engine = None
        if _background_engine:
            await _background_engine.dispose()
            _background_engine = None
        
        _session_maker = None
        _background_session_maker = None
        
        logger.info("✅ Database engines disposed (Vercel compatible)")
    except Exception as e:
        logger.warning(f"Engine cleanup warning (normal in serverless): {e}")