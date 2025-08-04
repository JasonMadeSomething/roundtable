import openai
from sqlalchemy.orm import Session
from sqlalchemy import func
import numpy as np
import os

from app.models import Turn, Chunk, Document, Conversation

# OpenAI API key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GPT_MODEL = "gpt-4"
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI's text-embedding-ada-002
MAX_CHUNKS = 10  # Maximum number of chunks to retrieve


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


async def retrieve_relevant_chunks(query: str, conversation_id: int, db: Session, limit: int = MAX_CHUNKS):
    """Retrieve chunks relevant to the query"""
    # Generate embedding for query
    query_embedding = await generate_embedding(query)
    
    # Get document IDs for this conversation
    document_ids = [doc_id for doc_id, in db.query(Document.id).filter(Document.conversation_id == conversation_id).all()]
    
    if not document_ids:
        return []
    
    # Retrieve relevant chunks using cosine similarity
    # Note: In a real implementation with pgvector, we would use the vector similarity search
    # For now, we'll simulate it by retrieving all chunks and sorting by similarity
    chunks = db.query(Chunk).filter(Chunk.document_id.in_(document_ids)).all()
    
    # Calculate cosine similarity
    chunk_similarities = []
    for chunk in chunks:
        if chunk.embedding:
            similarity = cosine_similarity(query_embedding, chunk.embedding)
            chunk_similarities.append((chunk, similarity))
    
    # Sort by similarity (descending)
    chunk_similarities.sort(key=lambda x: x[1], reverse=True)
    
    # Return top chunks
    return [chunk for chunk, _ in chunk_similarities[:limit]]


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)


async def generate_turn_response(conversation_id: int, turn_number: int, query: str = None, db: Session = None):
    """Generate a response for a conversation turn"""
    # Get conversation name
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    conversation_name = conversation.name if conversation else f"Conversation {conversation_id}"
    
    # Get previous turns
    previous_turns = []
    if turn_number > 1:
        previous_turns = db.query(Turn).filter(
            Turn.conversation_id == conversation_id,
            Turn.turn_number < turn_number
        ).order_by(Turn.turn_number).all()
    
    # Prepare context
    context = f"Conversation: {conversation_name}\n\n"
    
    # Add previous turns to context
    if previous_turns:
        context += "Previous turns:\n"
        for turn in previous_turns:
            context += f"Turn {turn.turn_number}: {turn.response}\n\n"
    
    # For the first turn, use the query to retrieve relevant chunks
    # For subsequent turns, use the last turn's response
    search_text = query if turn_number == 1 and query else (previous_turns[-1].response if previous_turns else "")
    
    # Retrieve relevant chunks
    relevant_chunks = await retrieve_relevant_chunks(search_text, conversation_id, db)
    
    # Add relevant chunks to context
    if relevant_chunks:
        context += "Relevant document chunks:\n"
        for chunk in relevant_chunks:
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            filename = document.filename if document else "Unknown"
            context += f"From {filename}, chunk {chunk.sequence_number}: {chunk.content}\n\n"
    
    # Prepare prompt
    if turn_number == 1:
        if query:
            prompt = f"You are participating in a multi-agent discourse system where you'll have a conversation with yourself about the provided documents. Here's the initial query: '{query}'. Based on the relevant document chunks, provide a thoughtful response."
        else:
            prompt = "You are participating in a multi-agent discourse system where you'll have a conversation with yourself about the provided documents. Start the conversation by introducing the topic based on the document chunks provided."
    else:
        prompt = "Continue the conversation by responding to your previous message. Consider both the conversation history and the relevant document chunks."
    
    # Generate response using OpenAI API
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        response = await openai.ChatCompletion.acreate(
            model=GPT_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": context}
            ],
            max_tokens=500,
            temperature=0.7
        )
        return response.choices[0].message.content
    else:
        # For development without API key, return a placeholder response
        return f"This is a placeholder response for turn {turn_number}. In a real implementation, this would be generated by OpenAI's GPT model based on the conversation context and relevant document chunks."
