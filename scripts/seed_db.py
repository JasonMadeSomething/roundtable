#!/usr/bin/env python3
"""
Database seeding script for Roundtable.
This script populates the database with sample data for development purposes.
"""

import os
import sys
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db import SessionLocal
from app.models import Conversation, Document, Chunk, Turn, ModelConfig
from app.services.document_processor import generate_embedding


# Sample model configurations
SAMPLE_MODEL_CONFIGS = [
    {
        "name": "Critical Analyst",
        "provider": "openai",
        "model_id": "gpt-4",
        "persona_name": "Critical Analyst",
        "persona_description": "A rigorous, skeptical thinker who questions assumptions and demands evidence",
        "persona_instructions": "Approach all claims with skepticism. Ask for evidence and challenge assumptions. Focus on logical inconsistencies and methodological flaws. Play devil's advocate.",
        "temperature": 0.7,
        "max_tokens": 500,
        "top_p": 1.0,
        "provider_parameters": '{"presence_penalty": 0.0, "frequency_penalty": 0.0}',
        "is_active": True
    },
    {
        "name": "Creative Synthesizer",
        "provider": "openai",
        "model_id": "gpt-4",
        "persona_name": "Creative Synthesizer",
        "persona_description": "An innovative thinker who connects disparate ideas and generates novel perspectives",
        "persona_instructions": "Look for unexpected connections between concepts. Generate novel hypotheses and perspectives. Think outside conventional frameworks. Propose creative solutions and analogies.",
        "temperature": 0.9,
        "max_tokens": 500,
        "top_p": 1.0,
        "provider_parameters": '{"presence_penalty": 0.2, "frequency_penalty": 0.3}',
        "is_active": True
    },
    {
        "name": "Empirical Scientist",
        "provider": "anthropic",
        "model_id": "claude-3-opus",
        "persona_name": "Empirical Scientist",
        "persona_description": "A data-driven researcher who prioritizes empirical evidence and methodological rigor",
        "persona_instructions": "Focus on empirical evidence and data. Evaluate the quality of research methods and statistical analyses. Distinguish between correlation and causation. Emphasize reproducibility and falsifiability.",
        "temperature": 0.5,
        "max_tokens": 500,
        "top_p": 0.95,
        "provider_parameters": '{"top_k": 40}',
        "is_active": True
    },
    {
        "name": "Philosophical Theorist",
        "provider": "deepseek",
        "model_id": "deepseek-chat",
        "persona_name": "Philosophical Theorist",
        "persona_description": "A conceptual thinker who explores fundamental questions and theoretical frameworks",
        "persona_instructions": "Examine fundamental assumptions and conceptual frameworks. Consider ethical implications and philosophical perspectives. Explore thought experiments and counterfactuals. Question the meaning of key terms and concepts.",
        "temperature": 0.8,
        "max_tokens": 500,
        "top_p": 1.0,
        "provider_parameters": '{"presence_penalty": 0.1}',
        "is_active": True
    }
]

# Sample data
SAMPLE_CONVERSATIONS = [
    {"name": "Philosophy Discussion"},
    {"name": "Scientific Research"},
    {"name": "Literary Analysis"}
]

SAMPLE_DOCUMENTS = [
    {
        "conversation_id": 1,
        "filename": "plato_republic.txt",
        "content": """
        The Republic is a Socratic dialogue, authored by Plato around 375 BCE, concerning justice, the order and character of the just city-state, and the just man.
        It is Plato's best-known work, and has proven to be one of the world's most influential works of philosophy and political theory, both intellectually and historically.
        In the dialogue, Socrates talks with various Athenians and foreigners about the meaning of justice and whether the just man is happier than the unjust man.
        They consider the natures of existing regimes and then propose a series of different, hypothetical cities in comparison, culminating in Kallipolis, a utopian city-state ruled by a philosopher-king.
        """
    },
    {
        "conversation_id": 2,
        "filename": "quantum_physics.txt",
        "content": """
        Quantum physics is the study of matter and energy at its most fundamental level.
        A central concept is that energy comes in indivisible packets called quanta.
        Quantum mechanics describes the behavior of matter and its interactions with energy on the scale of atoms and subatomic particles.
        It explains phenomena such as the wave-particle duality, quantum entanglement, and the uncertainty principle.
        The development of quantum mechanics in the early 20th century revolutionized our understanding of the physical world.
        """
    },
    {
        "conversation_id": 3,
        "filename": "shakespeare_hamlet.txt",
        "content": """
        Hamlet is a tragedy written by William Shakespeare sometime between 1599 and 1601.
        It is Shakespeare's longest play, with 30,557 words.
        Set in Denmark, the play depicts Prince Hamlet and his revenge against his uncle, Claudius, who has murdered Hamlet's father in order to seize his throne and marry Hamlet's mother.
        Hamlet is considered among the most powerful and influential works of world literature, with a story capable of "seemingly endless retelling and adaptation by others."
        It was one of Shakespeare's most popular works during his lifetime and still ranks among his most performed.
        """
    }
]

SAMPLE_TURNS = [
    {
        "conversation_id": 1,
        "turn_number": 1,
        "model_name": "gpt-4",
        "response": "Plato's Republic presents a fascinating exploration of justice and the ideal state. The dialogue format allows for a dynamic exchange of ideas between Socrates and his interlocutors. One of the central questions posed is whether the just person is happier than the unjust person, regardless of external rewards or punishments. This leads to an examination of different forms of government and the proposal of a utopian city-state ruled by philosopher-kings who possess true knowledge."
    },
    {
        "conversation_id": 1,
        "turn_number": 2,
        "model_name": "gpt-4",
        "response": "Building on my previous point, the concept of the philosopher-king is particularly intriguing. Plato argues that the ideal ruler must be a philosopher because only philosophers can grasp the Form of the Good and thus know what is truly best for the city. This raises important questions about the relationship between knowledge and power. Is specialized knowledge necessary for good governance? Should political power be reserved for those with certain kinds of expertise? These questions remain relevant in contemporary political discourse."
    }
]


async def seed_database():
    """Seed the database with sample data"""
    # Create a database session
    db = SessionLocal()
    
    try:
        print("Seeding database with sample data...")
        
        # Add model configurations
        for config_data in SAMPLE_MODEL_CONFIGS:
            model_config = ModelConfig(**config_data)
            db.add(model_config)
        db.commit()
        print(f"Added {len(SAMPLE_MODEL_CONFIGS)} sample model configurations")
        
        # Add conversations
        for conv_data in SAMPLE_CONVERSATIONS:
            conversation = Conversation(**conv_data)
            db.add(conversation)
        db.commit()
        print(f"Added {len(SAMPLE_CONVERSATIONS)} sample conversations")
        
        # Add documents
        for doc_data in SAMPLE_DOCUMENTS:
            document = Document(**doc_data)
            db.add(document)
        db.commit()
        print(f"Added {len(SAMPLE_DOCUMENTS)} sample documents")
        
        # Process documents into chunks
        for document in db.query(Document).all():
            # Simple sentence splitting for demo purposes
            sentences = [s.strip() for s in document.content.split('.') if s.strip()]
            
            # Create chunks
            for i, sentence in enumerate(sentences):
                chunk = Chunk(
                    document_id=document.id,
                    sequence_number=i + 1,
                    content=sentence
                )
                # Generate embedding
                embedding = await generate_embedding(sentence)
                chunk.embedding = embedding
                db.add(chunk)
            
            db.commit()
            print(f"Processed document {document.id} into {len(sentences)} chunks")
        
        # Add turns
        for turn_data in SAMPLE_TURNS:
            # For sample turns, assign a random model config
            model_config = db.query(ModelConfig).first()  # Just use the first one for simplicity
            if model_config:
                turn_data["model_config_id"] = model_config.id
            
            turn = Turn(**turn_data)
            db.add(turn)
        db.commit()
        print(f"Added {len(SAMPLE_TURNS)} sample turns")
        
        print("Database seeding completed successfully!")
        
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(seed_database())
