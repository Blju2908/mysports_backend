"""
Database utilities for LLM modules and standalone scripts.
Provides database connections outside of FastAPI context.
"""

import os
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from app.core.config import get_config

class DatabaseManager:
    """
    Manages database connections for standalone scripts and LLM modules.
    Separate from FastAPI's dependency injection system.
    """
    
    def __init__(self, use_production: bool = False):
        self.use_production = use_production
        self._engine = None
        self._session_factory = None
        
    def _get_database_url(self) -> str:
        """
        Ermittelt die richtige Datenbank-URL basierend auf der Konfiguration.
        
        Returns:
            Die Datenbank-URL für die Verbindung
        """
        config = get_config()
        
        if self.use_production:
            # Produktionsdatenbank (Supabase)
            db_url = config.SUPABASE_DB_URL
            if not db_url.startswith("postgresql+asyncpg://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            print(f"🚀 Verwende Produktionsdatenbank: {db_url.split('@')[1] if '@' in db_url else 'Supabase'}")
        else:
            # Lokale Entwicklungsdatenbank
            db_url = config.ALEMBIC_DB_URL
            if not db_url.startswith("postgresql+asyncpg://"):
                db_url = db_url.replace("postgresql://", "postgresql+asyncpg://")
            print(f"💻 Verwende lokale Entwicklungsdatenbank")
            
        return db_url
    
    def _create_engine(self):
        """Erstellt die SQLAlchemy Engine."""
        if self._engine is None:
            db_url = self._get_database_url()
            
            engine_args = {
                "echo": False,
            }

            if self.use_production:
                engine_args["poolclass"] = NullPool
                engine_args["connect_args"] = {
                    "statement_cache_size": 0,
                    "prepared_statement_cache_size": 0
                }
            else:
                engine_args.update({
                    "pool_size": 5,
                    "max_overflow": 10,
                    "pool_pre_ping": True,
                    "pool_recycle": 3600,
                })
            
            self._engine = create_async_engine(db_url, **engine_args)
            
            # Session Factory
            self._session_factory = sessionmaker(
                self._engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
        return self._engine
    
    async def get_session(self) -> AsyncSession:
        """
        Erstellt eine neue Datenbank-Session.
        
        Returns:
            Eine neue AsyncSession-Instanz
            
        Usage:
            db_manager = DatabaseManager(use_production=True)
            async with db_manager.get_session() as session:
                # Deine Datenbankoperationen hier
                result = await session.execute(select(Model))
        """
        if self._session_factory is None:
            self._create_engine()
            
        return self._session_factory()
    
    async def close(self):
        """Schließt die Engine und alle Verbindungen."""
        if self._engine:
            await self._engine.dispose()
            self._engine = None
            self._session_factory = None

# Convenience Functions für einfache Verwendung

async def get_production_session() -> AsyncSession:
    """
    Erstellt eine Session für die Produktionsdatenbank.
    
    Returns:
        AsyncSession für Produktionsdatenbank
        
    Usage:
        async with get_production_session() as session:
            # Deine Datenbankoperationen
            pass
    """
    manager = DatabaseManager(use_production=True)
    return await manager.get_session()

async def get_development_session() -> AsyncSession:
    """
    Erstellt eine Session für die Entwicklungsdatenbank.
    
    Returns:
        AsyncSession für Entwicklungsdatenbank
        
    Usage:
        async with get_development_session() as session:
            # Deine Datenbankoperationen
            pass
    """
    manager = DatabaseManager(use_production=False)
    return await manager.get_session()

async def create_db_session(use_production: bool = False) -> AsyncGenerator[AsyncSession, None]:
    """
    Context Manager für Datenbank-Sessions.
    Automatisches Schließen der Session nach Verwendung.
    
    Args:
        use_production: True für Produktions-DB, False für Entwicklungs-DB
        
    Yields:
        AsyncSession
        
    Usage:
        async for session in create_db_session(use_production=True):
            # Deine Datenbankoperationen
            result = await session.execute(select(Model))
            break  # Wichtig: break nach Operationen
    """
    manager = DatabaseManager(use_production=use_production)
    session = await manager.get_session()
    
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()
        await manager.close()

# Test-Funktion für Verbindungstest
async def test_database_connection(use_production: bool = False) -> bool:
    """
    Testet die Datenbankverbindung.
    
    Args:
        use_production: True für Produktions-DB, False für Entwicklungs-DB
        
    Returns:
        True wenn Verbindung erfolgreich, False sonst
    """
    try:
        print(f"🔍 Teste Datenbankverbindung ({'Produktion' if use_production else 'Entwicklung'})...")
        
        async for session in create_db_session(use_production=use_production):
            # Einfache Test-Query
            from sqlmodel import text
            result = await session.execute(text("SELECT 1 as test"))
            test_value = result.scalar()
            
            if test_value == 1:
                print("✅ Datenbankverbindung erfolgreich!")
                return True
            break
            
    except Exception as e:
        print(f"❌ Datenbankverbindung fehlgeschlagen: {e}")
        return False
    
    return False 