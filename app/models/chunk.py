from sqlalchemy import Column, Integer, Text, ForeignKey, String, Boolean, Float
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from .base import Base, TimestampMixin


class Chunk(Base, TimestampMixin):
    """Model for document chunks with vector embeddings and semantic structure metadata"""
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    sequence_number = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    # Using pgvector's Vector type for embeddings
    embedding = Column(Vector(1536), nullable=True)
    
    # Document structure metadata
    section_title = Column(String(255), nullable=True)  # Section title if this chunk is or contains a header
    is_section_header = Column(Boolean, default=False)  # Whether this chunk is a section header
    paragraph_id = Column(Integer, nullable=True)  # ID to group chunks from the same paragraph
    semantic_group = Column(String(255), nullable=True)  # Topic/entity cluster this chunk belongs to
    importance_score = Column(Float, nullable=True)  # Importance score (0-1) based on content significance
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    def __repr__(self):
        return f"<Chunk(id={self.id}, sequence_number={self.sequence_number}, semantic_group={self.semantic_group})>"
