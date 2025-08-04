from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    """Model for conversations"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    
    # Relationships
    documents = relationship("Document", back_populates="conversation", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, name={self.name})>"
