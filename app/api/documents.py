from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session
from typing import List
import os

from app.db import get_db
from app.models import Document, Conversation
from app.services.document_processor import process_document
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class DocumentResponse(BaseModel):
    id: int
    conversation_id: int
    filename: str
    created_at: datetime

    class Config:
        orm_mode = True


@router.post("/conversations/{conversation_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    conversation_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a document to a conversation"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Read file content
    content = await file.read()
    content_str = content.decode("utf-8")
    
    # Create document
    document = Document(
        conversation_id=conversation_id,
        filename=file.filename,
        content=content_str
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    
    # Process document (chunk and embed)
    await process_document(document.id, db)
    
    return document


@router.get("/conversations/{conversation_id}/documents", response_model=List[DocumentResponse])
def list_documents(conversation_id: int, db: Session = Depends(get_db)):
    """List all documents in a conversation"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    documents = db.query(Document).filter(Document.conversation_id == conversation_id).all()
    return documents


@router.get("/documents/{document_id}", response_model=DocumentResponse)
def get_document(document_id: int, db: Session = Depends(get_db)):
    """Get a specific document by ID"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: int, db: Session = Depends(get_db)):
    """Delete a document by ID"""
    document = db.query(Document).filter(Document.id == document_id).first()
    if document is None:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(document)
    db.commit()
    return None
