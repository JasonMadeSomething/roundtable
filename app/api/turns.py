from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models import Turn, Conversation
from app.services.agent_service import generate_turn_response
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class TurnCreate(BaseModel):
    query: Optional[str] = None  # Optional query for the first turn


class TurnResponse(BaseModel):
    id: int
    conversation_id: int
    turn_number: int
    model_name: str
    response: str
    created_at: datetime

    class Config:
        orm_mode = True


@router.post("/conversations/{conversation_id}/turns", response_model=TurnResponse, status_code=status.HTTP_201_CREATED)
async def create_turn(
    conversation_id: int,
    turn_data: TurnCreate,
    db: Session = Depends(get_db)
):
    """Create a new turn in a conversation"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get the last turn number for this conversation
    last_turn = db.query(Turn).filter(Turn.conversation_id == conversation_id).order_by(Turn.turn_number.desc()).first()
    turn_number = 1 if last_turn is None else last_turn.turn_number + 1
    
    # Generate response based on previous turns and relevant document chunks
    model_name = "gpt-4"  # Default model
    response = await generate_turn_response(
        conversation_id=conversation_id,
        turn_number=turn_number,
        query=turn_data.query if turn_number == 1 else None,
        db=db
    )
    
    # Create turn
    turn = Turn(
        conversation_id=conversation_id,
        turn_number=turn_number,
        model_name=model_name,
        response=response
    )
    db.add(turn)
    db.commit()
    db.refresh(turn)
    
    return turn


@router.get("/conversations/{conversation_id}/turns", response_model=List[TurnResponse])
def list_turns(conversation_id: int, db: Session = Depends(get_db)):
    """List all turns in a conversation"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    turns = db.query(Turn).filter(Turn.conversation_id == conversation_id).order_by(Turn.turn_number).all()
    return turns


@router.get("/turns/{turn_id}", response_model=TurnResponse)
def get_turn(turn_id: int, db: Session = Depends(get_db)):
    """Get a specific turn by ID"""
    turn = db.query(Turn).filter(Turn.id == turn_id).first()
    if turn is None:
        raise HTTPException(status_code=404, detail="Turn not found")
    return turn
