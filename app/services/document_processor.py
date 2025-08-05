from sqlalchemy.orm import Session
import spacy
import re
from typing import List, Dict

from app.models import Document, Chunk
from app.services.embedding_service import generate_embedding

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Chunking configuration
MAX_CHUNK_SIZE = 512  # Maximum number of characters per chunk
MIN_CHUNK_SIZE = 100  # Minimum number of characters per chunk
OVERLAP_SIZE = 50     # Number of characters to overlap between chunks


async def process_document(document_id: int, db: Session):
    """Process a document by chunking it and generating embeddings using spaCy"""
    # Get document
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise ValueError(f"Document with ID {document_id} not found")
    
    # Parse document with spaCy for linguistic analysis
    doc = nlp(document.content)
    
    # Extract document structure
    sections = extract_document_sections(doc)
    paragraphs = extract_paragraphs(doc)
    semantic_groups = identify_semantic_groups(doc)
    
    # Create semantic chunks
    chunks = create_semantic_chunks(
        doc=doc,
        document_id=document_id,
        sections=sections,
        paragraphs=paragraphs,
        semantic_groups=semantic_groups
    )
    
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


def extract_document_sections(doc) -> List[Dict]:
    """Extract sections and their headers from the document"""
    sections = []
    current_section = None
    current_section_text = []
    
    # Pattern for common section headers (e.g., "1. Introduction", "Chapter 1:", etc.)
    header_pattern = re.compile(r'^(?:\d+\.\s+|\w+\s+\d+:|Chapter\s+\d+:|Section\s+\d+:)\s*(.*)', re.IGNORECASE)
    
    for i, sent in enumerate(doc.sents):
        sent_text = sent.text.strip()
        
        # Check if this sentence looks like a section header
        is_header = False
        header_match = header_pattern.match(sent_text)
        
        # Check for header patterns
        if header_match:
            is_header = True
            header_text = header_match.group(1)
        # Check for short, capitalized sentences that might be headers
        elif len(sent_text) < 100 and sent_text.isupper():
            is_header = True
            header_text = sent_text
        # Check for sentences ending with a colon (potential headers)
        elif sent_text.endswith(':') and len(sent_text) < 100:
            is_header = True
            header_text = sent_text.rstrip(':')
        
        if is_header:
            # Save previous section if it exists
            if current_section is not None:
                sections.append({
                    'title': current_section,
                    'content': ' '.join(current_section_text),
                    'start_idx': i - len(current_section_text),
                    'end_idx': i - 1
                })
            
            # Start new section
            current_section = header_text
            current_section_text = []
        else:
            # Add to current section
            current_section_text.append(sent_text)
    
    # Add the last section
    if current_section is not None and current_section_text:
        sections.append({
            'title': current_section,
            'content': ' '.join(current_section_text),
            'start_idx': len(list(doc.sents)) - len(current_section_text),
            'end_idx': len(list(doc.sents)) - 1
        })
    elif current_section_text:  # Document has no sections but has content
        sections.append({
            'title': 'Main Content',
            'content': ' '.join(current_section_text),
            'start_idx': 0,
            'end_idx': len(list(doc.sents)) - 1
        })
    
    return sections


def extract_paragraphs(doc) -> List[Dict]:
    """Extract paragraphs from the document"""
    paragraphs = []
    current_paragraph = []
    paragraph_id = 1
    
    for i, sent in enumerate(doc.sents):
        sent_text = sent.text.strip()
        current_paragraph.append(sent_text)
        
        # Check for paragraph breaks (empty lines, etc.)
        next_sent = None
        if i < len(list(doc.sents)) - 1:
            next_sent_idx = i + 1
            for potential_next in doc.sents:
                if list(doc.sents).index(potential_next) == next_sent_idx:
                    next_sent = potential_next
                    break
        
        # If this is the last sentence or there's a paragraph break
        if next_sent is None or sent.end_char + 2 < next_sent.start_char:
            paragraphs.append({
                'id': paragraph_id,
                'content': ' '.join(current_paragraph),
                'start_idx': i - len(current_paragraph) + 1,
                'end_idx': i
            })
            paragraph_id += 1
            current_paragraph = []
    
    # Add the last paragraph if not already added
    if current_paragraph:
        paragraphs.append({
            'id': paragraph_id,
            'content': ' '.join(current_paragraph),
            'start_idx': len(list(doc.sents)) - len(current_paragraph),
            'end_idx': len(list(doc.sents)) - 1
        })
    
    return paragraphs


def identify_semantic_groups(doc) -> Dict[int, str]:
    """Identify semantic groups (topics/entities) for sentences"""
    semantic_groups = {}
    
    # Extract main entities and noun chunks
    main_entities = {}
    for ent in doc.ents:
        if ent.label_ in ['ORG', 'PERSON', 'GPE', 'LOC', 'PRODUCT', 'EVENT', 'WORK_OF_ART']:
            if ent.text not in main_entities:
                main_entities[ent.text] = []
            main_entities[ent.text].append(ent.start_char)
    
    # Group sentences by their main entities/topics
    for i, sent in enumerate(doc.sents):
        assigned_group = None
        
        # Check if sentence contains any main entities
        for entity, positions in main_entities.items():
            if any(pos >= sent.start_char and pos < sent.end_char for pos in positions):
                assigned_group = f"Topic: {entity}"
                break
        
        # If no entity found, use the main noun phrase as the topic
        if not assigned_group:
            main_nouns = [chunk.text for chunk in sent.noun_chunks]
            if main_nouns:
                assigned_group = f"Topic: {main_nouns[0]}"
            else:
                assigned_group = "General Content"
        
        semantic_groups[i] = assigned_group
    
    return semantic_groups


def create_semantic_chunks(doc, document_id: int, sections: List[Dict], 
                         paragraphs: List[Dict], semantic_groups: Dict[int, str]) -> List[Chunk]:
    """Create semantic chunks based on document structure and content"""
    from app.models import Chunk
    
    chunks = []
    sequence_number = 1
    
    # Map sentence indices to their paragraph IDs
    sent_to_paragraph = {}
    for para in paragraphs:
        for i in range(para['start_idx'], para['end_idx'] + 1):
            sent_to_paragraph[i] = para['id']
    
    # Map sentence indices to their section titles
    sent_to_section = {}
    for section in sections:
        for i in range(section['start_idx'], section['end_idx'] + 1):
            sent_to_section[i] = section['title']
    
    # Create chunks based on semantic coherence
    current_chunk_text = []
    current_chunk_sentences = []
    current_semantic_group = None
    current_paragraph_id = None
    current_section_title = None
    
    for i, sent in enumerate(doc.sents):
        sent_text = sent.text.strip()
        if not sent_text:  # Skip empty sentences
            continue
            
        # Get metadata for this sentence
        paragraph_id = sent_to_paragraph.get(i)
        section_title = sent_to_section.get(i)
        semantic_group = semantic_groups.get(i)
        
        # Check if this is a section header
        is_section_header = False
        for section in sections:
            if section['start_idx'] == i and i == section['start_idx']:
                is_section_header = True
                break
        
        # Determine if we should start a new chunk
        start_new_chunk = False
        
        # Start new chunk if this is a section header
        if is_section_header:
            start_new_chunk = True
        # Start new chunk if semantic group changes
        elif semantic_group != current_semantic_group and current_chunk_text:
            start_new_chunk = True
        # Start new chunk if paragraph changes
        elif paragraph_id != current_paragraph_id and current_chunk_text:
            start_new_chunk = True
        # Start new chunk if current chunk is getting too large
        elif len(' '.join(current_chunk_text)) + len(sent_text) > MAX_CHUNK_SIZE and current_chunk_text:
            start_new_chunk = True
        
        # Create a chunk from accumulated sentences if needed
        if start_new_chunk and current_chunk_text:
            chunk_text = ' '.join(current_chunk_text)
            
            # Calculate importance score based on entity density and sentence position
            entity_count = sum(1 for sent in current_chunk_sentences for ent in sent.ents)
            avg_entity_density = entity_count / len(current_chunk_sentences) if current_chunk_sentences else 0
            importance_score = min(1.0, avg_entity_density * 0.5 + 0.5 * (1 if current_section_title else 0))
            
            chunk = Chunk(
                document_id=document_id,
                sequence_number=sequence_number,
                content=chunk_text,
                section_title=current_section_title,
                is_section_header=False,  # This is for content chunks
                paragraph_id=current_paragraph_id,
                semantic_group=current_semantic_group,
                importance_score=importance_score
            )
            chunks.append(chunk)
            sequence_number += 1
            
            # Reset for next chunk
            current_chunk_text = []
            current_chunk_sentences = []
        
        # If this is a section header, create a special chunk for it
        if is_section_header:
            chunk = Chunk(
                document_id=document_id,
                sequence_number=sequence_number,
                content=sent_text,
                section_title=sent_text,
                is_section_header=True,
                paragraph_id=paragraph_id,
                semantic_group="Section Header",
                importance_score=1.0  # Headers are maximally important
            )
            chunks.append(chunk)
            sequence_number += 1
            
            # Update tracking variables
            current_chunk_text = []
            current_chunk_sentences = []
            current_semantic_group = semantic_group
            current_paragraph_id = paragraph_id
            current_section_title = section_title
        else:
            # Add to current chunk
            current_chunk_text.append(sent_text)
            current_chunk_sentences.append(sent)
            current_semantic_group = semantic_group
            current_paragraph_id = paragraph_id
            current_section_title = section_title
    
    # Add the last chunk if there's anything left
    if current_chunk_text:
        chunk_text = ' '.join(current_chunk_text)
        
        # Calculate importance score
        entity_count = sum(1 for sent in current_chunk_sentences for ent in sent.ents)
        avg_entity_density = entity_count / len(current_chunk_sentences) if current_chunk_sentences else 0
        importance_score = min(1.0, avg_entity_density * 0.5 + 0.5 * (1 if current_section_title else 0))
        
        chunk = Chunk(
            document_id=document_id,
            sequence_number=sequence_number,
            content=chunk_text,
            section_title=current_section_title,
            is_section_header=False,
            paragraph_id=current_paragraph_id,
            semantic_group=current_semantic_group,
            importance_score=importance_score
        )
        chunks.append(chunk)
    
    return chunks
