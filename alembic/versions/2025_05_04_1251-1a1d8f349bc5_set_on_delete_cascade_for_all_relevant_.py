"""Set ON DELETE CASCADE for all relevant foreign keys

Revision ID: 1a1d8f349bc5
Revises: d4726ff1edca
Create Date: 2025-05-04 12:51:25.636337

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = '1a1d8f349bc5'
down_revision: Union[str, None] = 'd4726ff1edca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # blocks.workout_id
    op.drop_constraint('blocks_workout_id_fkey', 'blocks', type_='foreignkey')
    op.create_foreign_key(
        'blocks_workout_id_fkey',
        'blocks', 'workouts',
        ['workout_id'], ['id'],
        ondelete='CASCADE'
    )
    # exercises.block_id
    op.drop_constraint('exercises_block_id_fkey', 'exercises', type_='foreignkey')
    op.create_foreign_key(
        'exercises_block_id_fkey',
        'exercises', 'blocks',
        ['block_id'], ['id'],
        ondelete='CASCADE'
    )
    # sets.exercise_id
    op.drop_constraint('sets_exercise_id_fkey', 'sets', type_='foreignkey')
    op.create_foreign_key(
        'sets_exercise_id_fkey',
        'sets', 'exercises',
        ['exercise_id'], ['id'],
        ondelete='CASCADE'
    )

def downgrade() -> None:
    # blocks.workout_id
    op.drop_constraint('blocks_workout_id_fkey', 'blocks', type_='foreignkey')
    op.create_foreign_key(
        'blocks_workout_id_fkey',
        'blocks', 'workouts',
        ['workout_id'], ['id']
    )
    # exercises.block_id
    op.drop_constraint('exercises_block_id_fkey', 'exercises', type_='foreignkey')
    op.create_foreign_key(
        'exercises_block_id_fkey',
        'exercises', 'blocks',
        ['block_id'], ['id']
    )
    # sets.exercise_id
    op.drop_constraint('sets_exercise_id_fkey', 'sets', type_='foreignkey')
    op.create_foreign_key(
        'sets_exercise_id_fkey',
        'sets', 'exercises',
        ['exercise_id'], ['id']
    )