import hashlib
import openai
import os
import numpy as np
from typing import List

# API keys and configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI's text-embedding-ada-002

def _deterministic_embedding(text: str) -> List[float]:
    """Generate a deterministic embedding using a hash of the text.

    This is used in development when ``OPENAI_API_KEY`` is not set. The
    resulting vector is repeatable for the same input but carries no semantic
    meaning.
    """
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    seed = int.from_bytes(digest[:8], "little")
    rng = np.random.default_rng(seed)
    return rng.uniform(-1, 1, EMBEDDING_DIMENSION).tolist()


async def generate_embedding(text: str) -> List[float]:
    """Generate embedding for text using OpenAI API.

    Falls back to a deterministic hash-based vector when ``OPENAI_API_KEY``
    is not provided. This fallback is intended only for local development
    and testing.
    """
    if not OPENAI_API_KEY:
        return _deterministic_embedding(text)
    
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
    """Synchronous version of ``generate_embedding`` for internal use.

    Mirrors the asynchronous function's behavior, including the deterministic
    fallback when ``OPENAI_API_KEY`` is unset.
    """
    if not OPENAI_API_KEY:
        return _deterministic_embedding(text)
    
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
