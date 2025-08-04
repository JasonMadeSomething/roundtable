"""Add model_config table and update turns

Revision ID: 002
Revises: 001
Create Date: 2025-08-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create model_configs table
    op.create_table(
        'model_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('model_id', sa.String(), nullable=False),
        sa.Column('persona_name', sa.String(), nullable=False),
        sa.Column('persona_description', sa.Text(), nullable=False),
        sa.Column('persona_instructions', sa.Text(), nullable=False),
        sa.Column('temperature', sa.Float(), nullable=False, server_default='0.7'),
        sa.Column('max_tokens', sa.Integer(), nullable=False, server_default='500'),
        sa.Column('top_p', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('provider_parameters', JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_model_configs_id'), 'model_configs', ['id'], unique=False)
    
    # Update turns table
    op.add_column('turns', sa.Column('model_config_id', sa.Integer(), nullable=True))
    op.add_column('turns', sa.Column('private_thoughts', sa.Text(), nullable=True))
    op.create_foreign_key('fk_turns_model_config', 'turns', 'model_configs', ['model_config_id'], ['id'])


def downgrade() -> None:
    # Remove foreign key constraint
    op.drop_constraint('fk_turns_model_config', 'turns', type_='foreignkey')
    
    # Remove columns from turns
    op.drop_column('turns', 'private_thoughts')
    op.drop_column('turns', 'model_config_id')
    
    # Drop model_configs table
    op.drop_index(op.f('ix_model_configs_id'), table_name='model_configs')
    op.drop_table('model_configs')
