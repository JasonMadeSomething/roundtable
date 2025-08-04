from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db import get_db
from app.models import Turn, Conversation, ModelConfig
from app.services.agent_service import generate_turn_response
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class TurnCreate(BaseModel):
    query: Optional[str] = None  # Optional query for the first turn
    model_config_id: Optional[int] = None  # Optional model config ID to use


class TurnResponse(BaseModel):
    id: int
    conversation_id: int
    turn_number: int
    model_name: str
    model_config_id: Optional[int] = None
    response: str
    private_thoughts: Optional[str] = None
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
    response, private_thoughts = await generate_turn_response(
        conversation_id=conversation_id,
        turn_number=turn_number,
        query=turn_data.query if turn_number == 1 else None,
        db=db,
        model_config_id=turn_data.model_config_id
    )
    
    # Get model config information
    model_config = None
    model_name = "gpt-4"  # Default model name for backward compatibility
    
    if turn_data.model_config_id:
        model_config = db.query(ModelConfig).filter(ModelConfig.id == turn_data.model_config_id).first()
        if model_config:
            model_name = f"{model_config.provider}/{model_config.model_id}"
    
    # Create turn
    turn = Turn(
        conversation_id=conversation_id,
        turn_number=turn_number,
        model_name=model_name,
        model_config_id=turn_data.model_config_id,
        response=response,
        private_thoughts=private_thoughts
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
