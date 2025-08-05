from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class PersonaVote(Base, TimestampMixin):
    """Model for storing votes from personas for the next turn"""
    __tablename__ = "persona_votes"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    turn_id = Column(Integer, ForeignKey("turns.id"), nullable=False)
    voter_model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False)
    voted_for_model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="persona_votes")
    turn = relationship("Turn", back_populates="votes_cast")
    voter = relationship("ModelConfig", foreign_keys=[voter_model_config_id])
    voted_for = relationship("ModelConfig", foreign_keys=[voted_for_model_config_id])
    
    # Ensure each persona votes only once per turn
    __table_args__ = (
        UniqueConstraint('turn_id', 'voter_model_config_id', name='uix_persona_vote_turn_voter'),
    )
    
    def __repr__(self):
        return f"<PersonaVote(turn_id={self.turn_id}, voter={self.voter_model_config_id}, voted_for={self.voted_for_model_config_id})>"
