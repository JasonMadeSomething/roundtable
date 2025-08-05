from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Conversation(Base, TimestampMixin):
    """Model for conversations"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    enable_voting = Column(Boolean, nullable=False, default=False)  # Whether personas can vote for next turn
    
    # Relationships
    documents = relationship("Document", back_populates="conversation", cascade="all, delete-orphan")
    turns = relationship("Turn", back_populates="conversation", cascade="all, delete-orphan")
    persona_orders = relationship("PersonaOrder", back_populates="conversation", cascade="all, delete-orphan")
    persona_votes = relationship("PersonaVote", back_populates="conversation", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, name={self.name})>"
