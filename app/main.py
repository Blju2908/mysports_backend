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
    """Vercel Serverless optimized lifespan"""
    engine = get_engine()
    
    # ✅ Vercel Serverless: Non-blocking startup - Test unified DB connection
    try:
        async with engine.begin() as conn:  # ✅ Using begin() for transaction
            await conn.execute(text("SELECT 1"))
        logger.info("✅ Vercel Pro: Unified Supabase connection successful (Session Mode 5432)")
    except Exception as e:
        logger.error(f"⚠️ Vercel Startup: Database connection test failed: {e}")
        # ✅ Don't crash - Vercel kann trotzdem starten
        logger.info("🔄 Continuing startup - DB connections will be established on demand")
    
    yield
    
    # ✅ Vercel Serverless: Graceful cleanup
    try:
        await close_engine()
        logger.info("✅ Vercel Shutdown: Database engines disposed")
    except Exception as e:
        logger.error(f"⚠️ Vercel Shutdown error: {e}")

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
    """Vercel Pro DB health check - Unified Supabase Session Mode"""
    try:
        engine = get_engine()
        async with engine.begin() as conn:  # ✅ Using begin() for proper transaction
            result = await conn.execute(text("SELECT 1"))
            if result.scalar() == 1:
                return {
                    "status": "ok", 
                    "database": "connected", 
                    "platform": "vercel_pro",
                    "mode": "unified_engine", 
                    "engine": "supabase_session_5432",
                    "config": "prepared_statements_enabled_better_performance"
                }
            return {"status": "error", "database": "query_failed"}
    except Exception as e:
        return {"status": "error", "database": "error", "error": str(e), "platform": "vercel_pro"}