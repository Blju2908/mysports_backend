from fastapi import FastAPI
from app.api import create_api_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.middleware.activity_logging_middleware import ActivityLoggingMiddleware
import os

# ✅ VERCEL COMPATIBLE: Load environment immediately (no lifespan needed)
load_dotenv()

# ✅ VERCEL COMPATIBLE: Simple FastAPI app without lifespan
# Lifespan events don't work properly on Vercel serverless functions
app = FastAPI(
    title="S3SSIONS API",
    description="Backend API for S3SSIONS fitness app",
    version="1.0.0"
)

# CORS-Konfiguration für das lokale Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Activity Logging Middleware hinzufügen
app.add_middleware(
    ActivityLoggingMiddleware,
    exclude_paths=["/docs", "/openapi.json", "/redoc", "/favicon.ico", "/health"]
)

app.include_router(create_api_router())

@app.get("/")
def read_root():
    return {"status": "ok", "message": "S3SSIONS API is running"}

@app.get("/health")
def health():
    """✅ VERCEL COMPATIBLE: Simple health check without database dependency"""
    return {
        "status": "ok", 
        "environment": os.getenv("ENVIRONMENT", "unknown"),
        "platform": "vercel" if os.getenv("VERCEL") else "local"
    }

@app.get("/health/db")
async def health_db():
    """✅ SUPABASE TRANSACTION MODE: Database health check"""
    try:
        from app.db.session import test_db_connection
        
        # Use the optimized test function
        is_connected = await test_db_connection()
        
        if is_connected:
            return {
                "status": "ok",
                "database": "connected",
                "connection_mode": "transaction_mode_6543",
                "platform": "vercel" if os.getenv("VERCEL") else "local"
            }
        else:
            return {
                "status": "error",
                "database": "disconnected",
                "connection_mode": "transaction_mode_6543",
                "platform": "vercel" if os.getenv("VERCEL") else "local"
            }
            
    except Exception as e:
        return {
            "status": "error",
            "database": "error",
            "error": str(e),
            "connection_mode": "transaction_mode_6543",
            "platform": "vercel" if os.getenv("VERCEL") else "local"
        }