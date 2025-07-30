# backend/scripts/utils/script_setup.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

def setup_environment():
    """
    Setup environment variables and Python path for scripts.
    Call this at the beginning of any script that needs access to the app.
    """
    # Get the backend directory (parent of scripts)
    backend_dir = Path(__file__).parent.parent.parent
    
    # Add backend directory to Python path so we can import app modules
    if str(backend_dir) not in sys.path:
        sys.path.insert(0, str(backend_dir))
    
    # Load environment variables
    env_file = backend_dir / ".env.development"
    if env_file.exists():
        load_dotenv(env_file)
    else:
        # Fallback to .env if .env.development doesn't exist
        fallback_env = backend_dir / ".env"
        if fallback_env.exists():
            load_dotenv(fallback_env)

# Import the engine after environment setup
def get_engine():
    """Get the database engine after environment is set up"""
    from app.db.session import engine
    return engine

@asynccontextmanager
async def get_standalone_session() -> AsyncSession:
    """
    Stellt eine unabhängige, asynchrone DB-Session für Skripte bereit.
    Diese Funktion ist hier, damit du nur noch eine Datei importieren musst.
    """
    engine = get_engine()
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()