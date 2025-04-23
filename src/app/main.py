from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api import create_api_router
from dotenv import load_dotenv
@asynccontextmanager
async def lifespan(app):
    load_dotenv()
    # Hier können Startup-Tasks (z.B. DB-Init, LLM-Cache) platziert werden
    yield
    # Hier können Shutdown-Tasks platziert werden

app = FastAPI(lifespan=lifespan)
app.include_router(create_api_router())

@app.get("/")
def read_root():
    return {"status": "ok"}

@app.get("/health")
def health():
    return {"status": "ok"}