"""New migration

Revision ID: 70563d1f1831
Revises: 700ab5c3090d
Create Date: 2025-04-23 20:20:34.221868

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '70563d1f1831'
down_revision: Union[str, None] = '700ab5c3090d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('sets_block_id_fkey', 'sets', type_='foreignkey')
    op.drop_column('sets', 'block_id')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('sets', sa.Column('block_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.create_foreign_key('sets_block_id_fkey', 'sets', 'blocks', ['block_id'], ['id'])
    # ### end Alembic commands ###
