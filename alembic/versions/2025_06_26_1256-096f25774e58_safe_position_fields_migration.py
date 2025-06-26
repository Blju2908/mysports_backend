"""Safe position fields migration

Revision ID: 096f25774e58
Revises: 40e8acb1436a
Create Date: 2025-06-26 12:56:19.123456

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '096f25774e58'
down_revision: Union[str, None] = '40e8acb1436a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Connect to database to check current state
    connection = op.get_bind()
    
    # Function to safely add column if it doesn't exist
    def add_column_if_not_exists(table_name: str, column_name: str):
        # Check if column exists
        result = connection.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='{table_name}' AND column_name='{column_name}'
        """))
        
        if not result.fetchone():
            # Column doesn't exist, add it
            op.add_column(table_name, sa.Column(column_name, sa.Integer(), nullable=True, server_default='0'))
            print(f"✅ Added {column_name} to {table_name}")
        else:
            print(f"⏭️  Column {column_name} already exists in {table_name}")
    
    # Safely add position columns to all tables
    add_column_if_not_exists('blocks', 'position')
    add_column_if_not_exists('exercises', 'position') 
    add_column_if_not_exists('sets', 'position')
    
    # Update any NULL position values to sequential values
    # This ensures existing data gets proper positions
    connection.execute(text("""
        UPDATE blocks SET position = subquery.row_num - 1
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY workout_id ORDER BY id) as row_num
            FROM blocks WHERE position IS NULL
        ) AS subquery
        WHERE blocks.id = subquery.id;
    """))
    
    connection.execute(text("""
        UPDATE exercises SET position = subquery.row_num - 1
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY block_id ORDER BY id) as row_num
            FROM exercises WHERE position IS NULL
        ) AS subquery
        WHERE exercises.id = subquery.id;
    """))
    
    connection.execute(text("""
        UPDATE sets SET position = subquery.row_num - 1
        FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY exercise_id ORDER BY id) as row_num
            FROM sets WHERE position IS NULL
        ) AS subquery
        WHERE sets.id = subquery.id;
    """))
    
    print("✅ Position fields migration completed successfully!")


def downgrade() -> None:
    # Only drop columns if they exist
    connection = op.get_bind()
    
    def drop_column_if_exists(table_name: str, column_name: str):
        result = connection.execute(text(f"""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='{table_name}' AND column_name='{column_name}'
        """))
        
        if result.fetchone():
            op.drop_column(table_name, column_name)
            print(f"✅ Dropped {column_name} from {table_name}")
    
    drop_column_if_exists('sets', 'position')
    drop_column_if_exists('exercises', 'position')
    drop_column_if_exists('blocks', 'position')
