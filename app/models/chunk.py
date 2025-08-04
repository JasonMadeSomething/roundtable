from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import Float

from .base import Base, TimestampMixin


class Chunk(Base, TimestampMixin):
    """Model for document chunks with vector embeddings"""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # pgvector will be used for the embedding column, but we'll define it in the Alembic migration
    # since SQLAlchemy doesn't have native pgvector support
    embedding = Column(ARRAY(Float), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, sequence_number={self.sequence_number})>"
