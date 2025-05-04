from supabase import create_async_client
from app.core.config import get_config

async def get_supabase_client():
    config = get_config()
    return await create_async_client(config.SUPABASE_URL, config.SUPABASE_API_KEY) 