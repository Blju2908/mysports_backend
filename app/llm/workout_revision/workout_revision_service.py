# from typing import Dict, Any, Optional
# from uuid import UUID
# from sqlalchemy.ext.asyncio import AsyncSession
# from app.models.workout_model import Workout
# from app.services.workout_service import get_workout_details
# from app.llm.workout_revision.workout_revision_chain import revise_workout_two_step
# from app.models.training_plan_model import TrainingPlan
# from sqlmodel import select
# from app.llm.workout_generation.create_workout_service import (
#     format_training_plan_for_llm, 
#     format_training_history_for_llm,
#     replace_workout_atomically
# )
# from app.db.workout_db_access import get_training_history_for_user_from_db


# def workout_to_dict(workout: Workout) -> Dict[str, Any]:
#     """
#     Konvertiert ein Workout-Objekt in ein Dictionary für das LLM.
#     """
#     workout_dict = {
#         "id": workout.id,
#         "name": workout.name,
#         "description": workout.description,
#         "duration": workout.duration,
#         "focus": workout.focus,
#         "notes": workout.notes,
#         "date_created": workout.date_created.isoformat() if workout.date_created else None,
#         "blocks": []
#     }
    
#     # Process blocks
#     if workout.blocks:
#         for block in workout.blocks:
#             block_dict = {
#                 "id": block.id,
#                 "name": block.name,
#                 "description": block.description,
#                 "notes": block.notes,
#                 "position": getattr(block, "position", 0),
#                 "is_amrap": getattr(block, "is_amrap", False),
#                 "amrap_duration_minutes": getattr(block, "amrap_duration_minutes", None),
#                 "exercises": []
#             }
            
#             # Process exercises
#             if block.exercises:
#                 for exercise in block.exercises:
#                     exercise_dict = {
#                         "id": exercise.id,
#                         "name": exercise.name,
#                         "description": exercise.description,
#                         "notes": exercise.notes,
#                         "superset_id": exercise.superset_id,
#                         "position": getattr(exercise, "position", 0),
#                         "sets": []
#                     }
                    
#                     # Process sets
#                     if exercise.sets:
#                         for set_obj in exercise.sets:
#                             set_dict = {
#                                 "id": set_obj.id,
#                                 "weight": set_obj.weight,
#                                 "reps": set_obj.reps,
#                                 "duration": set_obj.duration,
#                                 "distance": set_obj.distance,
#                                 "rest_time": set_obj.rest_time,
#                                 "position": getattr(set_obj, "position", 0),
#                                 "status": set_obj.status.value if hasattr(set_obj.status, 'value') else str(set_obj.status),
#                                 "completed_at": set_obj.completed_at.isoformat() if set_obj.completed_at else None
#                             }
#                             exercise_dict["sets"].append(set_dict)
                    
#                     block_dict["exercises"].append(exercise_dict)
            
#             workout_dict["blocks"].append(block_dict)
    
#     return workout_dict


# async def run_workout_revision_chain(
#     workout_id: int,
#     user_feedback: str,
#     user_id: UUID,
#     db: AsyncSession,
#     save_to_db: bool = True,
# ) -> Workout:
#     """
#     ✅ REFACTORED: Führt die Workout-Revision Chain aus und speichert das Ergebnis als JSON.
#     WICHTIG: Überschreibt NICHT das Original-Workout, sondern speichert Revision in JSON-Spalte.
    
#     Args:
#         workout_id: ID des zu überarbeitenden Workouts
#         user_feedback: Feedback/Kommentar des Users
#         user_id: User ID für Kontext und Trainingsplan-Laden
#         db: Database Session (REQUIRED)
#         save_to_db: Wenn True, wird das revidierte Workout in der JSON-Spalte gespeichert
        
#     Returns:
#         Workout: Das Workout-Objekt mit gespeicherten Revision-Daten
        
#     Raises:
#         ValueError: Bei fehlenden Parametern oder Workout nicht gefunden
#         Exception: Bei LLM- oder DB-Fehlern
#     """
#     if not db:
#         raise ValueError("Database session is required")
    
#     try:
#         # 1. Lade den Trainingsplan aus der DB (analog zu run_workout_chain)
#         formatted_training_plan = None
        
#         training_plan_db_obj = await db.scalar(
#             select(TrainingPlan).where(TrainingPlan.user_id == user_id)
#         )
#         if training_plan_db_obj:
#             formatted_training_plan = format_training_plan_for_llm(training_plan_db_obj)
        
#         # 2. Lade die Trainingshistorie (analog zu run_workout_chain)
#         formatted_history = None
#         raw_training_history = await get_training_history_for_user_from_db(user_id, db, limit=10)
#         if raw_training_history:
#             formatted_history = format_training_history_for_llm(raw_training_history)
        
#         # 3. Lade das bestehende Workout aus der Datenbank
#         existing_workout_obj = await get_workout_details(
#             workout_id=workout_id,
#             db=db
#         )
        
#         # 4. Konvertiere das Workout in ein Dictionary für das LLM
#         existing_workout_dict = workout_to_dict(existing_workout_obj)
        
#         # 5. Führe die Revision Chain aus (2-Stufen)
#         revised_workout_schema = await revise_workout_two_step(
#             existing_workout=existing_workout_dict,
#             user_feedback=user_feedback,
#             training_plan=formatted_training_plan,
#             training_history=formatted_history
#         )
        
#         # 6. ✅ NEW: Speichere das revidierte Workout als JSON (ÜBERSCHREIBT NICHT DAS ORIGINAL!)
#         if save_to_db:
#             try:
#                 # Store revision as JSON in the revised_workout_data column
#                 existing_workout_obj.set_revision_data(revised_workout_schema.model_dump())
                
#                 # Add to session and commit
#                 db.add(existing_workout_obj)
#                 await db.commit()
#                 await db.refresh(existing_workout_obj)
                
#                 print(f"✅ Workout revision saved as JSON for workout ID: {existing_workout_obj.id}")
#                 return existing_workout_obj
                
#             except Exception as e:
#                 await db.rollback()
#                 print(f"❌ Fehler bei JSON-Revision-Speicherung: {str(e)}")
#                 raise
#         else:
#             # Falls save_to_db=False, geben wir das ursprüngliche Workout zurück
#             return existing_workout_obj
        
#     except Exception as e:
#         print(f"Error in run_workout_revision_chain: {e}")
#         import traceback
#         traceback.print_exc()
#         raise


# async def get_workout_for_revision(
#     workout_id: int,
#     db: AsyncSession
# ) -> Dict[str, Any]:
#     """
#     Lädt ein Workout für die Revision und gibt es als Dictionary zurück.
    
#     Args:
#         workout_id: ID des Workouts
#         db: Database Session
        
#     Returns:
#         Dict: Workout als Dictionary
        
#     Raises:
#         Exception: Bei DB-Fehlern oder Workout nicht gefunden
#     """
#     try:
#         workout_obj = await get_workout_details(
#             workout_id=workout_id,
#             db=db
#         )
        
#         return workout_to_dict(workout_obj)
        
#     except Exception as e:
#         print(f"Error in get_workout_for_revision: {e}")
#         raise


# async def accept_workout_revision(
#     workout_id: int,
#     user_id: UUID,
#     db: AsyncSession
# ) -> Workout:
#     """
#     ✅ IMPROVED: Akzeptiert eine Workout-Revision und überschreibt das Original atomisch.
#     Nutzt die bewährte replace_workout_atomically() Funktion für vollständige Ersetzung.
    
#     Args:
#         workout_id: ID des Workouts
#         user_id: User ID für Autorisierung
#         db: Database Session
        
#     Returns:
#         Workout: Das aktualisierte Workout-Objekt mit allen Subkomponenten
        
#     Raises:
#         ValueError: Wenn keine Revision vorhanden ist
#         Exception: Bei DB-Fehlern
#     """
#     try:
#         # 1. Lade das Workout
#         workout_obj = await get_workout_details(workout_id=workout_id, db=db)
        
#         # 2. Prüfe ob Revision vorhanden ist
#         if not workout_obj.has_pending_revision():
#             raise ValueError("No pending revision found for this workout")
        
#         # 3. Lade die Revision-Daten
#         revision_data = workout_obj.get_revision_data()
#         if not revision_data:
#             raise ValueError("No revision data available")
        
#         # 4. ✅ IMPROVED: Atomische Ersetzung des Workouts mit Revision-Daten
#         updated_workout = await replace_workout_atomically(
#             db=db,
#             workout_id=workout_id,
#             user_id=user_id,
#             new_workout_data=revision_data,
#             training_plan_id=workout_obj.training_plan_id  # Behalte Training Plan Referenz
#         )
        
#         # 5. ✅ NEW: Lösche die Revision-Daten nach erfolgreicher Ersetzung
#         updated_workout.clear_revision()
        
#         # 6. Final commit für Revision-Clearing
#         db.add(updated_workout)
#         await db.commit()
#         await db.refresh(updated_workout)
        
#         print(f"✅ Workout revision atomically accepted for workout ID: {updated_workout.id}")
#         return updated_workout
        
#     except Exception as e:
#         await db.rollback()
#         print(f"❌ Fehler bei Accept-Workout-Revision: {str(e)}")
#         raise 