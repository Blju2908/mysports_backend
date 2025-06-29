#!/usr/bin/env python3
"""
Migration Script: Migrate Training Plan User IDs

This script migrates the user_id field in training_plans table based on the existing
training_plan_id field in the users table.

Usage:
    python scripts/migrate_training_plan_user_ids.py [--production]

Args:
    --production: Run migration on production database (default: development)
"""

import asyncio
import argparse
import sys
import os
from typing import List, Tuple

# Add the parent directory to the path so we can import from app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import select
from app.llm.utils.db_utils import create_db_session, test_database_connection
from app.models.user_model import UserModel
from app.models.training_plan_model import TrainingPlan


async def migrate_training_plan_user_ids(use_production: bool = False) -> Tuple[int, int]:
    """
    Migriert die user_id Felder in der training_plans Tabelle basierend auf
    den bestehenden training_plan_id Feldern in der users Tabelle.
    
    Args:
        use_production: True für Produktions-DB, False für Entwicklungs-DB
        
    Returns:
        Tuple[migrated_count, total_users_with_plans]: Anzahl migrierter Pläne und Gesamtanzahl
    """
    migrated_count = 0
    errors = []
    
    print(f"🚀 Starte Migration der Training Plan User IDs...")
    print(f"📊 Verwende {'Produktions' if use_production else 'Entwicklungs'}-Datenbank")
    
    async for session in create_db_session(use_production=use_production):
        try:
            # Alle User mit training_plan_id holen
            print("📋 Lade User mit Training Plans...")
            result = await session.execute(
                select(UserModel).where(UserModel.training_plan_id.is_not(None))
            )
            users_list = result.scalars().all()
            
            print(f"👥 Gefunden: {len(users_list)} User mit Training Plans")
            
            if not users_list:
                print("ℹ️  Keine User mit Training Plans gefunden. Migration beendet.")
                return 0, 0
            
            # Für jeden User den entsprechenden TrainingPlan aktualisieren
            for i, user in enumerate(users_list, 1):
                try:
                    print(f"🔄 Verarbeite User {i}/{len(users_list)}: {user.id}")
                    
                    # TrainingPlan mit der entsprechenden ID finden
                    training_plan = await session.get(TrainingPlan, user.training_plan_id)
                    
                    if training_plan:
                        # Prüfen ob user_id bereits gesetzt ist
                        if training_plan.user_id is not None:
                            print(f"⚠️  Training Plan {training_plan.id} hat bereits user_id: {training_plan.user_id}")
                            continue
                        
                        # user_id setzen
                        training_plan.user_id = user.id
                        session.add(training_plan)
                        migrated_count += 1
                        
                        print(f"✅ Training Plan {training_plan.id} -> User {user.id}")
                    else:
                        error_msg = f"❌ Training Plan {user.training_plan_id} für User {user.id} nicht gefunden"
                        print(error_msg)
                        errors.append(error_msg)
                        
                except Exception as e:
                    error_msg = f"❌ Fehler bei User {user.id}: {e}"
                    print(error_msg)
                    errors.append(error_msg)
            
            # Änderungen committen
            if migrated_count > 0:
                print(f"💾 Speichere {migrated_count} Änderungen...")
                await session.commit()
                print("✅ Migration erfolgreich abgeschlossen!")
            else:
                print("ℹ️  Keine Änderungen zu speichern.")
            
            break  # Verlasse die Session
            
        except Exception as e:
            print(f"❌ Kritischer Fehler bei der Migration: {e}")
            await session.rollback()
            raise
    
    # Zusammenfassung
    print("\n" + "="*50)
    print("📊 MIGRATION ZUSAMMENFASSUNG")
    print("="*50)
    print(f"✅ Erfolgreich migriert: {migrated_count}")
    print(f"👥 Gesamt User mit Plans: {len(users_list)}")
    
    if errors:
        print(f"❌ Fehler: {len(errors)}")
        for error in errors:
            print(f"   {error}")
    
    return migrated_count, len(users_list)


async def verify_migration(use_production: bool = False) -> bool:
    """
    Verifiziert dass die Migration korrekt durchgeführt wurde.
    
    Args:
        use_production: True für Produktions-DB, False für Entwicklungs-DB
        
    Returns:
        True wenn Verifikation erfolgreich, False sonst
    """
    print("\n🔍 Verifiziere Migration...")
    
    async for session in create_db_session(use_production=use_production):
        try:
            # Alle User mit training_plan_id
            result1 = await session.execute(
                select(UserModel).where(UserModel.training_plan_id.is_not(None))
            )
            users_list = result1.scalars().all()
            
            # Alle TrainingPlans mit user_id
            result2 = await session.execute(
                select(TrainingPlan).where(TrainingPlan.user_id.is_not(None))
            )
            plans_list = result2.scalars().all()
            
            print(f"👥 User mit Training Plans: {len(users_list)}")
            print(f"📋 Training Plans mit User ID: {len(plans_list)}")
            
            # Prüfe Konsistenz
            mismatches = 0
            for user in users_list:
                plan = await session.get(TrainingPlan, user.training_plan_id)
                if plan and plan.user_id != user.id:
                    print(f"❌ Inkonsistenz: User {user.id} -> Plan {plan.id} hat user_id {plan.user_id}")
                    mismatches += 1
            
            if mismatches == 0:
                print("✅ Verifikation erfolgreich - alle Daten konsistent!")
                return True
            else:
                print(f"❌ Verifikation fehlgeschlagen - {mismatches} Inkonsistenzen gefunden!")
                return False
            
        except Exception as e:
            print(f"❌ Fehler bei der Verifikation: {e}")
            return False
        
        break  # Verlasse die Session


async def main():
    """Hauptfunktion für das Migration Script."""
    parser = argparse.ArgumentParser(description='Migrate Training Plan User IDs')
    parser.add_argument('--production', action='store_true', 
                      help='Run migration on production database')
    parser.add_argument('--verify-only', action='store_true',
                      help='Only verify migration, do not migrate')
    
    args = parser.parse_args()
    
    print("🔧 Training Plan User ID Migration Script")
    print("="*50)
    
    # Teste Datenbankverbindung
    if not await test_database_connection(use_production=args.production):
        print("❌ Datenbankverbindung fehlgeschlagen. Bitte Konfiguration prüfen.")
        return 1
    
    if args.verify_only:
        # Nur Verifikation
        success = await verify_migration(use_production=args.production)
        return 0 if success else 1
    
    # Warnung für Produktionsdatenbank
    if args.production:
        response = input("⚠️  WARNUNG: Du führst die Migration auf der PRODUKTIONSDATENBANK aus!\n"
                        "Bist du sicher? (ja/nein): ")
        if response.lower() not in ['ja', 'yes', 'y']:
            print("❌ Migration abgebrochen.")
            return 1
    
    try:
        # Migration durchführen
        migrated, total = await migrate_training_plan_user_ids(use_production=args.production)
        
        # Verifikation
        if migrated > 0:
            verification_success = await verify_migration(use_production=args.production)
            if not verification_success:
                print("❌ Migration wurde durchgeführt, aber Verifikation fehlgeschlagen!")
                return 1
        
        print(f"\n🎉 Migration erfolgreich abgeschlossen: {migrated}/{total} Training Plans migriert!")
        return 0
        
    except Exception as e:
        print(f"❌ Migration fehlgeschlagen: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 