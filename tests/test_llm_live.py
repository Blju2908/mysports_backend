
import httpx
import asyncio
import os
import json
from utils import login_supabase

# Basis-URL des laufenden FastAPI-Servers
BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000/v2") # Kann immer noch aus env gelesen werden oder hier hartkodiert werden

# Supabase Test-Benutzerdaten (HARTKODIERT)
TEST_USER_EMAIL = "julian@bloechl.io"
TEST_USER_PASSWORD = "DimeP2908!"

async def test_start_workout_creation_live():
    """
    Testet das Starten der Workout-Erstellung über einen laufenden FastAPI-Server.
    """
    # if not TEST_USER_EMAIL or not TEST_USER_PASSWORD: # Nicht mehr benötigt, da hartkodiert
    #     raise ValueError("TEST_USER_EMAIL or TEST_USER_PASSWORD not set.")

    print(f"\n--- Testing start_workout_creation live against: {BASE_URL} ---")

    try:
        # 1. Bei Supabase einloggen, um einen JWT-Token zu erhalten
        jwt_token = await login_supabase(TEST_USER_EMAIL, TEST_USER_PASSWORD)
        
        headers = {
            "Authorization": f"Bearer {jwt_token}",
            "Content-Type": "application/json"
        }

        # 2. Payload für die Workout-Erstellung
        start_payload = {
            "prompt": "Erstelle mir ein Home-Workout",
            "profile_id": 33956,
            "duration_minutes": 20
        }

        # 3. Request an den Endpoint senden
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE_URL}/llm/start-workout-creation", 
                headers=headers, 
                json=start_payload
            )
            response.raise_for_status() # Löst Ausnahme für 4xx/5xx Antworten aus
            
            response_data = response.json()
            print(f"Response from /llm/start-workout-creation: {json.dumps(response_data, indent=2)}")

            # Minimale Überprüfung
            assert response_data.get("success") is True
            assert "workout_id" in response_data.get("data", {})
            assert "log_id" in response_data.get("data", {})
            print("Workout creation initiated successfully!")

    except httpx.HTTPStatusError as e:
        print(f"HTTP Error: {e.response.status_code} - {e.response.text}")
    except httpx.RequestError as e:
        print(f"Request Error: {e}")
    except ValueError as e:
        print(f"Configuration Error: {e}")
    except AssertionError:
        print("Assertion failed: Response did not match expected successful structure.")

if __name__ == "__main__":
    asyncio.run(test_start_workout_creation_live()) 