"""New migration

Revision ID: 8f2b264a870f
Revises: a90356a832a5
Create Date: 2025-04-29 16:11:47.254453

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '8f2b264a870f'
down_revision: Union[str, None] = 'a90356a832a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('blocks', 'status')
    op.drop_column('workouts', 'status')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('workouts', sa.Column('status', postgresql.ENUM('INCOMPLETE', 'COMPLETED', name='workoutstatus'), autoincrement=False, nullable=False))
    op.add_column('blocks', sa.Column('status', postgresql.ENUM('incomplete', 'in_progress', 'complete', name='blockstatus'), autoincrement=False, nullable=False))
    # ### end Alembic commands ###
