from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Document(Base, TimestampMixin):
    """Model for documents"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    filename = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename})>"
