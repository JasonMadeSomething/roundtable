from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Turn(Base, TimestampMixin):
    """Model for conversation turns"""
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    model_name = Column(String, nullable=False)
    response = Column(Text, nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="turns")
    
    def __repr__(self):
        return f"<Turn(id={self.id}, turn_number={self.turn_number})>"
