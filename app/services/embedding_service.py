import openai
import os
import numpy as np
from typing import List

# API keys and configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI's text-embedding-ada-002

async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API"""
    if not OPENAI_API_KEY:
        # For development without API key, generate random embeddings
        return list(np.random.uniform(-1, 1, EMBEDDING_DIMENSION))
    
    # Set OpenAI API key
    openai.api_key = OPENAI_API_KEY
    
    # Generate embedding
    response = await openai.Embedding.acreate(
        input=text,
        model=EMBEDDING_MODEL
    )
    
    # Extract embedding
    embedding = response["data"][0]["embedding"]
    
    return embedding

def generate_embedding_sync(text: str) -> List[float]:
    """Synchronous version of generate_embedding for internal use"""
    if not OPENAI_API_KEY:
        # For development without API key, generate random embeddings
        return list(np.random.uniform(-1, 1, EMBEDDING_DIMENSION))
    
    # Set OpenAI API key
    openai.api_key = OPENAI_API_KEY
    
    # Generate embedding
    response = openai.Embedding.create(
        input=text,
        model=EMBEDDING_MODEL
    )
    
    # Extract embedding
    embedding = response["data"][0]["embedding"]
    
    return embedding
