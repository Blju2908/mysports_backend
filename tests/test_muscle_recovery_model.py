import os
from datetime import datetime

# Schritt 1: Importiere und initialisiere alles mit einer Zeile!
# Wir müssen den Pfad zu 'scripts' hinzufügen, um das neue Modul zu finden
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'scripts')))
from utils.project_setup import initialize_project_env, get_standalone_session, Environment

# Initialisiere die Entwicklungsumgebung
initialize_project_env(env=Environment.DEVELOPMENT)

# Schritt 2: Importiere deine App-Module wie gewohnt
from app.services.muscle_recorvery_model import MuscleRecoveryModel
from app.schemas.workout_schema import ExerciseRead

def test_load_and_process_exercises():
    """
    Testet das Laden und Verarbeiten von Übungsdaten.
    """
    recovery_model = MuscleRecoveryModel()

    # Der Pfad wird jetzt vom Projekt-Root aus gebildet, was robuster ist
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    json_file_path = os.path.join(project_root, "outputs", "exercises_with_done_sets_20250729_135938.json")
    
    print(f"\nVersuche, Daten von: {json_file_path} zu laden...")
    recovery_model.load_exercises_from_json(json_file_path)

    # Überprüfe, ob Daten geladen wurden
    assert hasattr(recovery_model, 'exercises_data')
    assert isinstance(recovery_model.exercises_data, list)
    assert len(recovery_model.exercises_data) > 0, "Es wurden keine Übungsdaten geladen."

    print("\n--- Aufruf von calculate_fatigue_level ---")
    recovery_model.calculate_fatigue_level(recovery_model.exercises_data)
    print("✅ calculate_fatigue_level aufgerufen.")
        
    print("\nErgebnis der (noch leeren) Ermüdungsberechnung:")
    print(recovery_model.muscle_groups)

    print("\nTest erfolgreich abgeschlossen! ✨")

async def test_db_connection():
    """
    Ein Beispiel, wie du die DB-Verbindung im Testskript nutzen kannst.
    """
    print("\n--- Teste DB-Verbindung ---")
    async with get_standalone_session() as db:
        # Du kannst hier jede DB-Operation durchführen
        from sqlmodel import select
        from app.models.user_model import UserModel
        user = await db.scalar(select(UserModel))
        assert user is not None
        print(f"✅ Erfolgreich mit DB verbunden und einen User gefunden: {user.id}")

if __name__ == "__main__":
    test_load_and_process_exercises()
    
    # Um den asynchronen DB-Test auszuführen:
    import asyncio
    asyncio.run(test_db_connection()) 