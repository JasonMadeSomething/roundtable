from sqlalchemy import Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class Turn(Base, TimestampMixin):
    """Model for conversation turns"""
    __tablename__ = "turns"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    turn_number = Column(Integer, nullable=False)
    model_name = Column(String, nullable=False)  # Kept for backward compatibility
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=True)  # New field
    response = Column(Text, nullable=False)
    private_thoughts = Column(Text, nullable=True)  # For dual-track conversations
    
    # Relationships
    conversation = relationship("Conversation", back_populates="turns")
    model_config = relationship("ModelConfig", back_populates="turns")
    
    def __repr__(self):
        return f"<Turn(id={self.id}, turn_number={self.turn_number})>"
