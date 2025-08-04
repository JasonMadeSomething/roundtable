import openai
from sqlalchemy.orm import Session
import numpy as np
import os
import random
import json
from typing import List

from app.models import Turn, Chunk, Document, Conversation, ModelConfig

# API keys and configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Default models
DEFAULT_OPENAI_MODEL = "gpt-4"
DEFAULT_ANTHROPIC_MODEL = "claude-3-opus-20240229"
DEFAULT_DEEPSEEK_MODEL = "deepseek-chat"

# Embedding configuration
EMBEDDING_MODEL = "text-embedding-ada-002"
EMBEDDING_DIMENSION = 1536  # Dimension of OpenAI's text-embedding-ada-002

# Retrieval configuration
MAX_CHUNKS = 10  # Maximum number of chunks to retrieve

# Multi-query RAG configuration
QUERY_TYPES = ["claim", "question", "disagreement"]

# Conflict scoring thresholds
MIN_DISAGREEMENT_SCORE = 0.3  # Minimum disagreement score to consider models in disagreement
MAX_AGREEMENT_SCORE = 0.8    # Maximum agreement score to consider models in agreement


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


async def multi_query_retrieval(base_query: str, conversation_id: int, db: Session, limit: int = MAX_CHUNKS) -> List[Chunk]:
    """Generate multiple query variants and retrieve relevant chunks using all of them"""
    # Generate query variants
    query_variants = [
        f"Key claim: {base_query}",  # Focus on factual claims
        f"Important question: {base_query}",  # Focus on interrogative aspects
        f"Potential disagreement: {base_query}"  # Focus on contentious points
    ]
    
    all_chunks = []
    seen_chunk_ids = set()
    
    # Retrieve chunks for each query variant
    for query in query_variants:
        chunks = await retrieve_relevant_chunks(query, conversation_id, db, limit=limit//len(query_variants))
        for chunk in chunks:
            if chunk.id not in seen_chunk_ids:
                all_chunks.append(chunk)
                seen_chunk_ids.add(chunk.id)
    
    # If we have fewer chunks than the limit, fill with standard retrieval
    if len(all_chunks) < limit:
        standard_chunks = await retrieve_relevant_chunks(base_query, conversation_id, db, limit=limit)
        for chunk in standard_chunks:
            if chunk.id not in seen_chunk_ids and len(all_chunks) < limit:
                all_chunks.append(chunk)
                seen_chunk_ids.add(chunk.id)
    
    return all_chunks

async def retrieve_relevant_chunks(query: str, conversation_id: int, db: Session, limit: int = MAX_CHUNKS):
    """Retrieve chunks relevant to the query using vector similarity search"""
    # Get document IDs for this conversation
    document_ids = [doc_id for doc_id, in db.query(Document.id).filter(Document.conversation_id == conversation_id).all()]
    
    if not document_ids:
        return []
    
    # Generate embedding for the query
    query_embedding = await generate_embedding(query)
    
    # Use pgvector's cosine similarity operator (<#>) to find relevant chunks
    # Lower score means higher similarity with cosine distance
    chunks = db.query(Chunk).filter(
        Chunk.document_id.in_(document_ids),
        Chunk.embedding.is_not(None)  # Ensure embedding exists
    ).order_by(
        Chunk.embedding.cosine_distance(query_embedding)
    ).limit(limit).all()
    
    return chunks


def cosine_similarity(vec1, vec2):
    """Calculate cosine similarity between two vectors"""
    dot_product = np.dot(vec1, vec2)
    norm1 = np.linalg.norm(vec1)
    norm2 = np.linalg.norm(vec2)
    return dot_product / (norm1 * norm2)


def calculate_disagreement_score(response1: str, response2: str) -> float:
    """Calculate a disagreement score between two responses
    
    This is a simplified implementation. In a production system, you would use
    more sophisticated NLP techniques or a model to calculate disagreement.
    """
    # For now, we'll use a simple heuristic based on cosine similarity of embeddings
    # In a real implementation, you would use a more sophisticated approach
    # such as using a model to evaluate disagreement or analyzing semantic content
    
    # Convert responses to embeddings
    embedding1 = np.array(generate_embedding_sync(response1))
    embedding2 = np.array(generate_embedding_sync(response2))
    
    # Calculate cosine similarity
    similarity = cosine_similarity(embedding1, embedding2)
    
    # Convert similarity to disagreement score (1 - similarity)
    disagreement = 1.0 - similarity
    
    return disagreement

def generate_embedding_sync(text: str) -> list:
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

async def select_model_for_turn(conversation_id: int, turn_number: int, db: Session) -> ModelConfig:
    """Select a model for the current turn using rotation and disagreement maximization"""
    # Get all active model configurations
    model_configs = db.query(ModelConfig).filter(ModelConfig.is_active).all()
    
    # If no model configs, create a default one
    if not model_configs:
        default_model = ModelConfig(
            name="Default GPT-4",
            provider="openai",
            model_id="gpt-4",
            persona_name="Neutral Analyst",
            persona_description="A neutral, analytical thinker who examines evidence carefully.",
            persona_instructions="Analyze the provided information carefully and provide a balanced perspective.",
            temperature=0.7,
            max_tokens=500,
            top_p=1.0,
            provider_parameters=json.dumps({}),
            is_active=True
        )
        db.add(default_model)
        db.commit()
        return default_model
    
    # For the first turn, select randomly
    if turn_number == 1:
        return random.choice(model_configs)
    
    # For subsequent turns, try to maximize disagreement
    previous_turn = db.query(Turn).filter(
        Turn.conversation_id == conversation_id,
        Turn.turn_number == turn_number - 1
    ).first()
    
    if not previous_turn or not previous_turn.model_config_id:
        return random.choice(model_configs)
    
    # Don't use the same model as the previous turn
    available_models = [m for m in model_configs if m.id != previous_turn.model_config_id]
    if not available_models:
        available_models = model_configs
    
    # If we have more than 2 turns, try to maximize disagreement
    if turn_number > 2:
        # Get the last two turns
        last_turns = db.query(Turn).filter(
            Turn.conversation_id == conversation_id,
            Turn.turn_number >= turn_number - 2,
            Turn.turn_number < turn_number
        ).order_by(Turn.turn_number).all()
        
        if len(last_turns) >= 2:
            # Calculate disagreement scores for each available model with the previous turn
            model_scores = []
            for model in available_models:
                # We would ideally predict disagreement here, but for now we'll use past performance
                # if this model was used before in this conversation
                model_turns = db.query(Turn).filter(
                    Turn.conversation_id == conversation_id,
                    Turn.model_config_id == model.id
                ).all()
                
                if model_turns:
                    # Calculate average disagreement with other turns
                    disagreement_scores = []
                    for mt in model_turns:
                        for other_turn in db.query(Turn).filter(
                            Turn.conversation_id == conversation_id,
                            Turn.id != mt.id,
                            Turn.turn_number < turn_number
                        ).all():
                            score = calculate_disagreement_score(mt.response, other_turn.response)
                            disagreement_scores.append(score)
                    
                    avg_disagreement = sum(disagreement_scores) / len(disagreement_scores) if disagreement_scores else 0.5
                    model_scores.append((model, avg_disagreement))
                else:
                    # No history for this model, assign a neutral score
                    model_scores.append((model, 0.5))
            
            # Sort by disagreement score (descending)
            model_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Return the model with the highest disagreement score
            if model_scores:
                return model_scores[0][0]
    
    # If we can't calculate disagreement or it's an early turn, just rotate
    return random.choice(available_models)

async def generate_turn_response(conversation_id: int, turn_number: int, query: str = None, db: Session = None, model_config_id: int = None):
    """Generate a response for a conversation turn"""
    # Get conversation name
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    conversation_name = conversation.name if conversation else f"Conversation {conversation_id}"
    
    # Select model for this turn if not specified
    model_config = None
    if model_config_id:
        model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()
    
    if not model_config:
        model_config = await select_model_for_turn(conversation_id, turn_number, db)
    
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
    
    # Use multi-query RAG to retrieve relevant chunks
    relevant_chunks = await multi_query_retrieval(search_text, conversation_id, db)
    
    # Add relevant chunks to context
    if relevant_chunks:
        context += "Relevant document chunks:\n"
        for chunk in relevant_chunks:
            document = db.query(Document).filter(Document.id == chunk.document_id).first()
            filename = document.filename if document else "Unknown"
            context += f"From {filename}, chunk {chunk.sequence_number}: {chunk.content}\n\n"
    
    # Prepare persona-specific prompt based on the selected model
    persona_name = model_config.persona_name
    persona_description = model_config.persona_description
    persona_instructions = model_config.persona_instructions
    
    # Determine which previous turns to include based on blind history pattern
    # For now, we'll use a simple pattern: only show the last 2 turns
    visible_turns = previous_turns[-2:] if len(previous_turns) > 2 else previous_turns
    
    # Prepare system prompt with persona information
    system_prompt = f"""You are {persona_name}, {persona_description}

You are participating in a multi-agent discourse system where multiple AI models with different perspectives discuss documents.

IMPORTANT GUIDELINES:
1. Maintain your unique perspective and analytical approach
2. Do NOT seek consensus - productive disagreement is the goal
3. Challenge assumptions and claims when appropriate
4. Focus on evidence from the provided document chunks
5. {persona_instructions}

Provide TWO separate responses:
- PRIVATE THOUGHTS: Your analytical process and reasoning (not shown to other agents)
- PUBLIC RESPONSE: Your formal contribution to the discourse (shown to other agents)
"""
    
    # Add turn-specific instructions
    if turn_number == 1:
        if query:
            system_prompt += f"\n\nThis is the first turn. Address the initial query: '{query}'. Based on the relevant document chunks, provide your perspective."
        else:
            system_prompt += "\n\nThis is the first turn. Start the conversation by introducing the topic based on the document chunks provided."
    else:
        # Find points of potential disagreement with previous turns
        disagreement_points = "\n\nConsider these potential points of disagreement:\n"
        for i, turn in enumerate(visible_turns):
            disagreement_points += f"- Response from Turn {turn.turn_number}: {turn.response[:100]}...\n"
        
        system_prompt += f"\n\nThis is turn {turn_number}. Respond to the previous messages, focusing on areas where you might have a different perspective or interpretation.{disagreement_points}"
    
    # Generate response using the appropriate API based on the model provider
    provider = model_config.provider.lower()
    model_id = model_config.model_id
    temperature = model_config.temperature
    max_tokens = model_config.max_tokens
    top_p = model_config.top_p
    provider_params = json.loads(model_config.provider_parameters) if model_config.provider_parameters else {}
    
    response_text = ""
    private_thoughts = ""
    
    try:
        if provider == "openai":
            if not OPENAI_API_KEY:
                return (f"[Placeholder] This is a response from {persona_name} for turn {turn_number}.", 
                        f"[Placeholder] These are private thoughts for turn {turn_number}.")
            
            openai.api_key = OPENAI_API_KEY
            response = await openai.ChatCompletion.acreate(
                model=model_id,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": context}
                ],
                max_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                **provider_params
            )
            full_response = response.choices[0].message.content
            
        elif provider == "anthropic":
            if not ANTHROPIC_API_KEY:
                return (f"[Placeholder] This is a response from {persona_name} for turn {turn_number}.", 
                        f"[Placeholder] These are private thoughts for turn {turn_number}.")
                
            # Implementation for Anthropic Claude API would go here
            # This is a placeholder for now
            full_response = f"[Placeholder] This is a response from Claude for turn {turn_number}.\n\nPRIVATE THOUGHTS: These are my analytical thoughts.\n\nPUBLIC RESPONSE: This is my public response."
            
        elif provider == "deepseek":
            if not DEEPSEEK_API_KEY:
                return (f"[Placeholder] This is a response from {persona_name} for turn {turn_number}.", 
                        f"[Placeholder] These are private thoughts for turn {turn_number}.")
                
            # Implementation for DeepSeek API would go here
            # This is a placeholder for now
            full_response = f"[Placeholder] This is a response from DeepSeek for turn {turn_number}.\n\nPRIVATE THOUGHTS: These are my analytical thoughts.\n\nPUBLIC RESPONSE: This is my public response."
            
        else:
            # Default to a placeholder response for unknown providers
            full_response = f"[Placeholder] This is a response from {persona_name} for turn {turn_number}.\n\nPRIVATE THOUGHTS: These are my analytical thoughts.\n\nPUBLIC RESPONSE: This is my public response."
        
        # Parse the response to separate private thoughts from public response
        if "PRIVATE THOUGHTS:" in full_response and "PUBLIC RESPONSE:" in full_response:
            # Extract private thoughts
            private_start = full_response.find("PRIVATE THOUGHTS:") + len("PRIVATE THOUGHTS:")
            private_end = full_response.find("PUBLIC RESPONSE:")
            private_thoughts = full_response[private_start:private_end].strip()
            
            # Extract public response
            public_start = full_response.find("PUBLIC RESPONSE:") + len("PUBLIC RESPONSE:")
            response_text = full_response[public_start:].strip()
        else:
            # If the model didn't follow the format, use the whole response as public
            response_text = full_response
            private_thoughts = "No private thoughts provided"
        
        return response_text, private_thoughts
        
    except Exception as e:
        # Log the error and return a fallback response
        print(f"Error generating response: {str(e)}")
        return (f"Error generating response from {persona_name}. Please try again.", 
                f"Error: {str(e)}")
