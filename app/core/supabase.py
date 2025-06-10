from supabase import create_async_client
from app.core.config import get_config

async def get_supabase_client(use_service_role: bool = False):
    config = get_config()
    key = config.SUPABASE_SERVICE_ROLE if use_service_role else config.SUPABASE_API_KEY
    return await create_async_client(config.SUPABASE_URL, key) 