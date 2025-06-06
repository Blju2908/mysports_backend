"""New migration

Revision ID: b5bd20d2f42b
Revises: 300fa80e0c38
Create Date: 2025-04-24 09:53:11.124051

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b5bd20d2f42b'
down_revision: Union[str, None] = '300fa80e0c38'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('blocks_workout_id_fkey', 'blocks', type_='foreignkey')
    op.create_foreign_key(None, 'blocks', 'workouts', ['workout_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('exercises_block_id_fkey', 'exercises', type_='foreignkey')
    op.create_foreign_key(None, 'exercises', 'blocks', ['block_id'], ['id'], ondelete='CASCADE')
    op.drop_constraint('sets_exercise_id_fkey', 'sets', type_='foreignkey')
    op.create_foreign_key(None, 'sets', 'exercises', ['exercise_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'sets', type_='foreignkey')
    op.create_foreign_key('sets_exercise_id_fkey', 'sets', 'exercises', ['exercise_id'], ['id'])
    op.drop_constraint(None, 'exercises', type_='foreignkey')
    op.create_foreign_key('exercises_block_id_fkey', 'exercises', 'blocks', ['block_id'], ['id'])
    op.drop_constraint(None, 'blocks', type_='foreignkey')
    op.create_foreign_key('blocks_workout_id_fkey', 'blocks', 'workouts', ['workout_id'], ['id'])
    # ### end Alembic commands ###
