from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class PersonaOrder(Base, TimestampMixin):
    """Model for storing the order of personas in a conversation"""
    __tablename__ = "persona_orders"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"), nullable=False)
    model_config_id = Column(Integer, ForeignKey("model_configs.id"), nullable=False)
    order_position = Column(Integer, nullable=False)  # 0-based position in the order
    
    # Relationships
    conversation = relationship("Conversation", back_populates="persona_orders")
    model_config = relationship("ModelConfig", back_populates="persona_orders")
    
    # Only enforce unique positions within a conversation so the same persona
    # can appear multiple times in the order (allowing an agent to "talk to
    # itself" or be configured in multiple slots).
    __table_args__ = (
        UniqueConstraint('conversation_id', 'order_position',
                         name='uix_persona_order_conversation_position'),
    )
    
    def __repr__(self):
        return f"<PersonaOrder(conversation_id={self.conversation_id}, model_config_id={self.model_config_id}, position={self.order_position})>"
