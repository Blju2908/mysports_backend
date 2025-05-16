from logging.config import fileConfig
import os  # Added import

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from dotenv import load_dotenv

from alembic import context
from sqlmodel import SQLModel
from app.models import (
    block_model,
    exercise_model,
    set_model,
    training_plan_model,
    user_model,
    workout_model,
    showcase_feedback_model,
    workout_feedback_model
)  # Ensure User model is registered in SQLModel.metadata

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata
target_metadata = SQLModel.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.

# Get environment and load the appropriate .env file
APP_ENV = "production"
env = os.getenv("APP_ENV", APP_ENV)
env_file = f".env.{env}"
load_dotenv(env_file)
print(f"Loading environment from {env_file}")

# Get Alembic DB URL from environment
alembic_url = os.getenv("ALEMBIC_DB_URL")
if not alembic_url:
    raise ValueError(f"ALEMBIC_DB_URL environment variable not set in {env_file}")

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    context.configure(
        url=alembic_url,  # Use the loaded ALEMBIC_DB_URL
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Create engine configuration dictionary manually
    engine_config = config.get_section(config.config_ini_section, {})
    engine_config["sqlalchemy.url"] = alembic_url # Inject the ALEMBIC_DB_URL

    connectable = engine_from_config(
        # config.get_section(config.config_ini_section, {}), <-- Replaced
        engine_config, # Use the manually created config dict
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
