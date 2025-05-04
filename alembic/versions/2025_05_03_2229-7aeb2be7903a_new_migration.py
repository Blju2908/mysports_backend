"""New migration

Revision ID: 7aeb2be7903a
Revises: 32abfdcf18bb
Create Date: 2025-05-03 22:29:04.777170

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision: str = '7aeb2be7903a'
down_revision: Union[str, None] = '32abfdcf18bb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Spalte auf TEXT casten (temporär)
    op.alter_column('blocks', 'status', type_=sa.Text(), postgresql_using="status::text")
    # 2. Altes Enum löschen
    op.execute("DROP TYPE IF EXISTS blockstatus")
    # 3. Neues Enum anlegen (mit Werten aus BlockStatus in block_model.py)
    op.execute("CREATE TYPE blockstatus AS ENUM ('open', 'done')")
    # 4. Spalte zurück auf Enum casten
    op.alter_column('blocks', 'status', type_=sa.Enum('open', 'done', name='blockstatus'), postgresql_using="status::blockstatus")
    # 5. Default und NOT NULL wiederherstellen
    op.alter_column('blocks', 'status', nullable=False, server_default=sa.text("'open'::blockstatus"))


def downgrade() -> None:
    # Rückwärts: auf TEXT casten, Enum löschen, ggf. alten Enum wiederherstellen
    op.alter_column('blocks', 'status', type_=sa.Text(), postgresql_using="status::text")
    op.execute("DROP TYPE IF EXISTS blockstatus")
    # Optional: alten Enum wiederherstellen, falls nötig
