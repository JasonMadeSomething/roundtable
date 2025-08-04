from sqlalchemy import Column, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, TimestampMixin


class Chunk(Base, TimestampMixin):
    """Model for document chunks with vector embeddings"""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Using pgvector's Vector type for embeddings
    embedding = Column(Vector(1536), nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, sequence_number={self.sequence_number})>"
