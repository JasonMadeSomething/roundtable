"""Fix enable_voting migration with default value

Revision ID: fix_enable_voting
Revises: ea956b3e4186
Create Date: 2025-08-04 18:55:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fix_enable_voting'
down_revision = 'ea956b3e4186'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First add the column as nullable
    op.add_column('conversations', sa.Column('enable_voting', sa.Boolean(), nullable=True))
    
    # Set default value for existing rows
    op.execute("UPDATE conversations SET enable_voting = FALSE")
    
    # Then make it not nullable
    op.alter_column('conversations', 'enable_voting', nullable=False)


def downgrade() -> None:
    op.drop_column('conversations', 'enable_voting')
