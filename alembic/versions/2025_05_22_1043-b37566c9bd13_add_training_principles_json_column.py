"""add training principles json column

Revision ID: b37566c9bd13
Revises: 7c213b629110
Create Date: 2025-05-22 10:43:38.647884

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
import sqlmodel


# revision identifiers, used by Alembic.
revision: str = 'b37566c9bd13'
down_revision: Union[str, None] = '7c213b629110'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('training_plans', sa.Column('training_principles_json', JSONB(), nullable=True))
    
    # Use a safer approach for converting the include_cardio column
    # First create a new boolean column
    op.execute('ALTER TABLE training_plans ADD COLUMN include_cardio_new BOOLEAN')
    
    # Then populate it with data converted from the old column
    op.execute("UPDATE training_plans SET include_cardio_new = CASE " +
               "WHEN include_cardio = 'yes' THEN TRUE " +
               "WHEN include_cardio = 'true' THEN TRUE " +
               "WHEN include_cardio = 't' THEN TRUE " +
               "ELSE FALSE END")
    
    # Drop the old column
    op.execute('ALTER TABLE training_plans DROP COLUMN include_cardio')
    
    # Rename the new column
    op.execute('ALTER TABLE training_plans RENAME COLUMN include_cardio_new TO include_cardio')
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    # For downgrade, use similar approach but convert boolean to varchar
    op.execute('ALTER TABLE training_plans ADD COLUMN include_cardio_old VARCHAR')
    
    # Convert boolean to string
    op.execute("UPDATE training_plans SET include_cardio_old = CASE " +
               "WHEN include_cardio = TRUE THEN 'yes' " +
               "ELSE 'no' END")
    
    # Drop boolean column
    op.execute('ALTER TABLE training_plans DROP COLUMN include_cardio')
    
    # Rename varchar column
    op.execute('ALTER TABLE training_plans RENAME COLUMN include_cardio_old TO include_cardio')
    
    # Drop JSON column
    op.drop_column('training_plans', 'training_principles_json')
    # ### end Alembic commands ###
