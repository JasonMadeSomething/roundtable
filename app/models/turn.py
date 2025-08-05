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
    next_turn_override_id = Column(Integer, ForeignKey("model_configs.id"), nullable=True)  # Override for next persona
    response = Column(Text, nullable=False)
    private_thoughts = Column(Text, nullable=True)  # For dual-track conversations
    
    # Relationships
    conversation = relationship("Conversation", back_populates="turns")
    model_config = relationship("ModelConfig", foreign_keys=[model_config_id], back_populates="turns")
    next_turn_override = relationship("ModelConfig", foreign_keys=[next_turn_override_id])
    votes_cast = relationship("PersonaVote", back_populates="turn", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Turn(id={self.id}, turn_number={self.turn_number})>"
