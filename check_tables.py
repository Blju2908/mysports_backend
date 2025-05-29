#!/usr/bin/env python3
"""
Script to check existing tables in the database
"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from app.core.config import Settings

async def check_tables():
    settings = Settings()
    engine = create_async_engine(settings.SUPABASE_DB_URL)
    
    try:
        async with engine.begin() as conn:
            # Check if landing_page_surveys table exists
            result = await conn.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name IN ('landing_page_surveys', 'users', 'alembic_version')
                ORDER BY table_name
            """))
            
            tables = result.fetchall()
            print("Existing tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # Check users table structure
            if any(table[0] == 'users' for table in tables):
                result = await conn.execute(text("""
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'users' 
                    AND table_schema = 'public'
                    ORDER BY column_name
                """))
                
                columns = result.fetchall()
                print("\nUsers table columns:")
                for column in columns:
                    print(f"  - {column[0]}: {column[1]}")
                    
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_tables()) 