"""New migration

Revision ID: 86d813f818ac
Revises: 45384e46fa73
Create Date: 2025-06-24 22:20:16.745941

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '86d813f818ac'
down_revision: Union[str, None] = '45384e46fa73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # Drop showcase_feedbacks first (it has foreign keys to the other tables)
    op.drop_table('showcase_feedbacks')
    # Then drop the tables it depends on
    op.drop_table('showcase_training_plans')
    # Drop index before dropping the table
    op.drop_index('ix_showcase_questionnaire_templates_questionnaire_id', table_name='showcase_questionnaire_templates')
    op.drop_table('showcase_questionnaire_templates')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('showcase_feedbacks',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('questionnaire_template_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('workout_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('training_plan_id', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('answers', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('feedback_comment', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('feedback_rating', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.ForeignKeyConstraint(['questionnaire_template_id'], ['showcase_questionnaire_templates.id'], name='showcase_feedbacks_questionnaire_template_id_fkey'),
    sa.ForeignKeyConstraint(['training_plan_id'], ['showcase_training_plans.id'], name='showcase_feedbacks_training_plan_id_fkey'),
    sa.ForeignKeyConstraint(['workout_id'], ['workouts.id'], name='showcase_feedbacks_workout_id_fkey'),
    sa.PrimaryKeyConstraint('id', name='showcase_feedbacks_pkey')
    )
    op.create_table('showcase_training_plans',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('goal', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('restrictions', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('equipment', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('session_duration', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('history', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='showcase_training_plans_pkey')
    )
    op.create_table('showcase_questionnaire_templates',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('questionnaire_id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), autoincrement=False, nullable=True),
    sa.Column('description', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('created_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.Column('updated_at', postgresql.TIMESTAMP(), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='showcase_questionnaire_templates_pkey')
    )
    op.create_index('ix_showcase_questionnaire_templates_questionnaire_id', 'showcase_questionnaire_templates', ['questionnaire_id'], unique=True)
    # ### end Alembic commands ###
