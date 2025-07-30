# backend/scripts/utils/project_setup.py
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from enum import Enum
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession

# Wir importieren die Engine direkt aus dem app-Modul
from app.db.session import engine

@asynccontextmanager
async def get_standalone_session() -> AsyncSession:
    """
    Stellt eine unabhängige, asynchrone DB-Session für Skripte bereit.
    Diese Funktion ist hier, damit du nur noch eine Datei importieren musst.
    """
    async with AsyncSession(engine) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()