import httpx
import os
from dotenv import load_dotenv
from pathlib import Path

# Lade Umgebungsvariablen aus der .env.production oder .env.test im Projekt-Root
# Stellen Sie sicher, dass diese Datei die Supabase-Schlüssel enthält.
BACKEND_DIR = Path(__file__).resolve().parents[1]
load_dotenv(os.path.join(BACKEND_DIR, '.env.development'))

async def login_supabase(email: str, password: str) -> str:
    """
    Authentifiziert sich bei Supabase und gibt den JWT-Token zurück.
    """

   
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_anon_key = os.getenv("SUPABASE_API_KEY")

    if not supabase_url or not supabase_anon_key:
        raise ValueError("SUPABASE_URL or SUPABASE_API_KEY not set in environment variables.")

    auth_url = f"{supabase_url}/auth/v1/token?grant_type=password"
    headers = {
        "apikey": supabase_anon_key,
        "Content-Type": "application/json"
    }
    payload = {
        "email": email,
        "password": password
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(auth_url, headers=headers, json=payload)
        response.raise_for_status() # Löst Ausnahme für 4xx/5xx Antworten aus
        data = response.json()
        
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("Authentication failed: No access_token received.")
        
        print(f"Successfully logged in as {email}. Token received (first 10 chars): {access_token[:10]}...")
        return access_token 