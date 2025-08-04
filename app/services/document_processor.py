import nltk
from nltk.tokenize import sent_tokenize
import openai
from sqlalchemy.orm import Session
import numpy as np
import os

from app.models import Document, Chunk

# Download NLTK data on first run
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI's text-embedding-ada-002


async def process_document(document_id: int, db: Session):
    """Process a document by chunking it and generating embeddings"""
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document with ID {document_id} not found")
    
    # Chunk document into sentences
    sentences = sent_tokenize(document.content)
    
    # Create chunks with sequence numbers
    chunks = []
    for i, sentence in enumerate(sentences):
        # Skip empty sentences
        if not sentence.strip():
            continue
        
        # Create chunk
        chunk = Chunk(
            document_id=document_id,
            sequence_number=i + 1,
            content=sentence,
        )
        chunks.append(chunk)
    
    # Add chunks to database
    db.add_all(chunks)
    db.commit()
    
    # Generate embeddings for chunks
    for chunk in chunks:
        embedding = await generate_embedding(chunk.content)
        chunk.embedding = embedding
    
    # Update chunks with embeddings
    db.commit()
    
    return len(chunks)


async def generate_embedding(text: str) -> list:
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
