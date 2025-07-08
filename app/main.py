from fastapi import FastAPI
from app.api import create_api_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.activity_logging_middleware import ActivityLoggingMiddleware
from contextlib import asynccontextmanager
import os
from sqlalchemy import text
from app.db.session import get_engine
import logging

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

# -------------------------------------------------------
# Lifespan context – initialises and disposes DB engine
# -------------------------------------------------------


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialise global SQLAlchemy engine once per container."""
    engine = get_engine()  # creates engine if not yet initialised

    # Optional: small health check on cold start
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection test successful")
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        raise

    # Store for later if needed
    app.state.engine = engine

    yield

    # Graceful shutdown
    try:
        await engine.dispose()
        logger.info("✅ SQLAlchemy engine disposed")
    except Exception as e:
        logger.warning(f"Engine disposal warning: {e}")


# FastAPI app instance
app = FastAPI(
    title="S3SSIONS API",
    description="Backend API for S3SSIONS fitness app",
    version="1.0.0",
    lifespan=lifespan,
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    ActivityLoggingMiddleware,
    exclude_paths=["/docs", "/openapi.json", "/redoc", "/favicon.ico", "/health"]
)

# Routes
app.include_router(create_api_router())

@app.get("/")
def read_root():
    return {"status": "ok", "message": "S3SSIONS API is running"}

@app.get("/health")
def health():
    return {
        "status": "ok", 
        "environment": os.getenv("ENVIRONMENT", "unknown")
    }

# --- Database health-check using SQLAlchemy engine


@app.get("/health/db")
async def health_db():
    """Simple database health check using the global engine."""
    engine = get_engine()
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return {
                    "status": "ok",
                    "database": "connected"
                }
            return {"status": "error", "database": "query_failed"}
    except Exception as e:
        return {"status": "error", "database": "error", "error": str(e)}