from sqlalchemy import Column, Integer, String, Boolean, Text, JSON, Float
from sqlalchemy.orm import relationship

from .base import Base, TimestampMixin


class ModelConfig(Base, TimestampMixin):
    """Model for AI model configurations"""
    __tablename__ = "model_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    provider = Column(String, nullable=False)  # e.g., 'openai', 'anthropic', 'deepseek'
    model_id = Column(String, nullable=False)  # e.g., 'gpt-4', 'claude-3-opus', 'deepseek-coder'
    
    # Persona configuration
    persona_name = Column(String, nullable=False)
    persona_description = Column(Text, nullable=False)
    persona_instructions = Column(Text, nullable=False)
    
    # Model parameters
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=500)
    top_p = Column(Float, nullable=False, default=1.0)
    
    # Additional parameters specific to each provider
    provider_parameters = Column(JSON, nullable=True)
    
    # Whether this model is active
    is_active = Column(Boolean, nullable=False, default=True)
    
    # Relationships
    turns = relationship("Turn", foreign_keys="Turn.model_config_id", back_populates="model_config")
    persona_orders = relationship("PersonaOrder", back_populates="model_config")
    
    def __repr__(self):
        return f"<ModelConfig(id={self.id}, name={self.name}, provider={self.provider}, model_id={self.model_id})>"
