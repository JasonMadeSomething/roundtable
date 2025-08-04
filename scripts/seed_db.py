#!/usr/bin/env python3
"""
Database seeding script for Roundtable.
This script populates the database with sample data for development purposes.
"""

import os
import sys
from datetime import datetime
import asyncio

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from app.db import engine, SessionLocal
from app.models import Base, Conversation, Document, Chunk, Turn
from app.services.document_processor import generate_embedding


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
