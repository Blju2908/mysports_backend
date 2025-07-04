"""New migration

Revision ID: 8fb5cb8f27c2
Revises: 096f25774e58
Create Date: 2025-06-29 20:32:22.994029

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '8fb5cb8f27c2'
down_revision: Union[str, None] = '096f25774e58'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('training_plans', sa.Column('user_id', sa.Uuid(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('training_plans', 'user_id')
    # ### end Alembic commands ###
