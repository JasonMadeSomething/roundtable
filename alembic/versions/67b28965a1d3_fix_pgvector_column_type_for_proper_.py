"""Fix pgvector column type for proper compatibility

Revision ID: 67b28965a1d3
Revises: 143af0674e3c
Create Date: 2025-08-04 15:47:45.818115

"""
from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '67b28965a1d3'
down_revision = '143af0674e3c'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop existing index if it exists
    op.execute('DROP INDEX IF EXISTS chunks_embedding_idx')
    
    # Recreate the embedding column with the proper Vector type
    op.execute('ALTER TABLE chunks DROP COLUMN IF EXISTS embedding')
    op.add_column('chunks', sa.Column('embedding', Vector(1536), nullable=True))
    
    # Create a proper vector index for cosine similarity search
    op.execute('CREATE INDEX chunks_embedding_idx ON chunks USING ivfflat (embedding vector_cosine_ops)')


def downgrade() -> None:
    # Drop the vector index
    op.execute('DROP INDEX IF EXISTS chunks_embedding_idx')
    
    # Revert to the original column type (ARRAY of Float)
    op.execute('ALTER TABLE chunks DROP COLUMN IF EXISTS embedding')
    op.add_column('chunks', sa.Column('embedding', sa.ARRAY(sa.Float()), nullable=True))
