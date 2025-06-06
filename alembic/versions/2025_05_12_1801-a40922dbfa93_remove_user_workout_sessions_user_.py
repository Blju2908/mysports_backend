"""remove user_workout_sessions, user_exercise_records, user_set_records tables

Revision ID: a40922dbfa93
Revises: 528707debe04
Create Date: 2025-05-12 18:01:30.272084

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a40922dbfa93'
down_revision: Union[str, None] = '528707debe04'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('user_set_records')
    op.drop_table('user_exercise_records')
    op.drop_table('user_workout_sessions')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user_set_records',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('exercise_record_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('original_set_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('weight', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('reps', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('duration', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('distance', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('speed', sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('rest_time', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('completed', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('notes', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_custom', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['exercise_record_id'], ['user_exercise_records.id'], name='user_set_records_exercise_record_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['original_set_id'], ['sets.id'], name='user_set_records_original_set_id_fkey', ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id', name='user_set_records_pkey')
    )
    op.create_table('user_exercise_records',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('session_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('original_exercise_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('name', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('is_custom', sa.BOOLEAN(), autoincrement=False, nullable=False),
    sa.Column('order', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['original_exercise_id'], ['exercises.id'], name='user_exercise_records_original_exercise_id_fkey', ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['session_id'], ['user_workout_sessions.id'], name='user_exercise_records_session_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='user_exercise_records_pkey')
    )
    op.create_table('user_workout_sessions',
    sa.Column('id', sa.INTEGER(), server_default=sa.text("nextval('user_workout_sessions_id_seq'::regclass)"), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), autoincrement=False, nullable=False),
    sa.Column('workout_id', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('started_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('completed_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=True),
    sa.Column('status', postgresql.ENUM('IN_PROGRESS', 'COMPLETED', 'ABANDONED', name='sessionstatus'), autoincrement=False, nullable=False),
    sa.Column('rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('duration_rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('intensity_rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('comment', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='user_workout_sessions_user_id_fkey', ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], name='user_workout_sessions_workout_id_fkey', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name='user_workout_sessions_pkey'),
    postgresql_ignore_search_path=False
    )
    # ### end Alembic commands ###
