from fastapi import FastAPI
from app.api import create_api_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.activity_logging_middleware import ActivityLoggingMiddleware
from contextlib import asynccontextmanager
import os
from sqlalchemy import text
from app.db.session import get_engine, close_engine
import logging

logger = logging.getLogger(__name__)

# Load environment
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and cleanup database engine"""
    engine = get_engine()
    
    # Test connection - Transaction Mode für schnelle API-Responses
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Database connection successful (Dual-Mode: API=Transaction, Background=Session)")
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        raise
    
    yield
    
    await close_engine()

# FastAPI app
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

@app.get("/health/db")
async def health_db():
    """Database health check - Dual Mode: API uses Transaction Mode (6543), Background uses Session Mode (5432)"""
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return {
                    "status": "ok", 
                    "database": "connected", 
                    "mode": "dual", 
                    "api_mode": "transaction_6543",
                    "background_mode": "session_5432"
                }
            return {"status": "error", "database": "query_failed"}
    except Exception as e:
        return {"status": "error", "database": "error", "error": str(e)}