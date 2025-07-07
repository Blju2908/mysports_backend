from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import create_api_router
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from app.db.session import create_db_and_tables, DatabaseManager
from app.middleware.activity_logging_middleware import ActivityLoggingMiddleware

@asynccontextmanager
async def lifespan(app):
    load_dotenv()
    # Startup-Tasks: DB-Init, LLM-Cache etc.
    await create_db_and_tables()  # Tabellen erstellen (nur für lokale Entwicklung/Migrationen)
    yield
    # Shutdown-Tasks
    await DatabaseManager.close_engine()

app = FastAPI(lifespan=lifespan)

# origins = [
#     "http://localhost:5173",
#     "https://www.s3ssions.com",
#     "https://s3ssions.com",
# ]

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
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}