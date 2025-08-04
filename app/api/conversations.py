from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db import get_db
from app.models import Conversation
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ConversationCreate(BaseModel):
    name: str


class ConversationResponse(BaseModel):
    id: int
    name: str
    created_at: datetime

    class Config:
        orm_mode = True


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
def create_conversation(conversation: ConversationCreate, db: Session = Depends(get_db)):
    """Create a new conversation"""
    db_conversation = Conversation(name=conversation.name)
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


@router.get("/conversations", response_model=List[ConversationResponse])
def list_conversations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """List all conversations"""
    conversations = db.query(Conversation).offset(skip).limit(limit).all()
    return conversations


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Get a specific conversation by ID"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conversation_id: int, db: Session = Depends(get_db)):
    """Delete a conversation by ID"""
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    db.delete(conversation)
    db.commit()
    return None
