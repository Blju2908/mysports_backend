"""
Script to force-stamp the database with the specified revision
"""
import os
import sys
from sqlalchemy import create_engine, text
from alembic.config import Config
from alembic import command
from dotenv import load_dotenv

# Load environment variables
APP_ENV = "production"
env_file = f".env.{APP_ENV}"
load_dotenv(env_file)
print(f"Loading environment from {env_file}")

# Get database URL
db_url = os.getenv("ALEMBIC_DB_URL")
if not db_url:
    print("ALEMBIC_DB_URL environment variable not set")
    sys.exit(1)

# Create Alembic config
alembic_cfg = Config("alembic.ini")

# Override the sqlalchemy.url with our own
alembic_cfg.set_main_option("sqlalchemy.url", db_url)

# Force stamp the database with the specified revision
TARGET_REVISION = "7c213b629110"  # This is the latest revision we want to stamp
print(f"Force stamping database with revision: {TARGET_REVISION}")

try:
    # Create the alembic_version table if it doesn't exist
    engine = create_engine(db_url)
    with engine.connect() as conn:
        conn.execute(text("CREATE TABLE IF NOT EXISTS alembic_version (version_num VARCHAR(32) NOT NULL)"))
        conn.execute(text("DELETE FROM alembic_version"))
        conn.execute(text(f"INSERT INTO alembic_version VALUES ('{TARGET_REVISION}')"))
        conn.commit()
    
    print("Successfully stamped database")
except Exception as e:
    print(f"Error stamping database: {e}")
    sys.exit(1)

# Now create a new migration
print("Creating new migration to add training_principles_json column...")
# We don't run command.revision here since we'll do it manually after

print("Done! Now you can run:")
print("python -m alembic revision --autogenerate -m \"add training principles json column\"")
print("python -m alembic upgrade head") 