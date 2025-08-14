from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from app.db import get_db
from app.models import Conversation, ModelConfig, PersonaOrder


router = APIRouter()


class PersonaOrderCreate(BaseModel):
    model_config_id: int
    order_position: int


class PersonaOrderUpdate(BaseModel):
    order_position: int


class PersonaOrderResponse(BaseModel):
    id: int
    conversation_id: int
    model_config_id: int
    order_position: int
    
    class Config:
        orm_mode = True


class ConversationPersonaOrdersUpdate(BaseModel):
    persona_orders: List[PersonaOrderCreate]


@router.post("/conversations/{conversation_id}/persona-orders", response_model=PersonaOrderResponse, status_code=status.HTTP_201_CREATED)
def create_persona_order(
    conversation_id: int, 
    persona_order: PersonaOrderCreate, 
    db: Session = Depends(get_db)
):
    """Add a persona to the conversation order"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if model config exists
    model_config = db.query(ModelConfig).filter(ModelConfig.id == persona_order.model_config_id).first()
    if not model_config:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    # Check if the position is already taken
    position_taken = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id,
        PersonaOrder.order_position == persona_order.order_position
    ).first()
    
    if position_taken:
        raise HTTPException(
            status_code=400, 
            detail=f"Position {persona_order.order_position} is already taken"
        )
    
    # Create new persona order
    db_persona_order = PersonaOrder(
        conversation_id=conversation_id,
        model_config_id=persona_order.model_config_id,
        order_position=persona_order.order_position
    )
    
    db.add(db_persona_order)
    db.commit()
    db.refresh(db_persona_order)
    
    return db_persona_order


@router.get("/conversations/{conversation_id}/persona-orders", response_model=List[PersonaOrderResponse])
def list_persona_orders(conversation_id: int, db: Session = Depends(get_db)):
    """List all personas in the conversation order"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Get all persona orders for this conversation
    persona_orders = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id
    ).order_by(PersonaOrder.order_position).all()
    
    return persona_orders


@router.put("/conversations/{conversation_id}/persona-orders/{order_id}", response_model=PersonaOrderResponse)
def update_persona_order(
    conversation_id: int,
    order_id: int,
    persona_order: PersonaOrderUpdate,
    db: Session = Depends(get_db)
):
    """Update a persona's position in the conversation order"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if the persona order exists
    db_persona_order = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id,
        PersonaOrder.id == order_id
    ).first()
    
    if not db_persona_order:
        raise HTTPException(status_code=404, detail="Persona order not found")
    
    # Check if the new position is already taken by another persona
    position_taken = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id,
        PersonaOrder.order_position == persona_order.order_position,
        PersonaOrder.id != order_id
    ).first()
    
    if position_taken:
        raise HTTPException(
            status_code=400, 
            detail=f"Position {persona_order.order_position} is already taken"
        )
    
    # Update the position
    db_persona_order.order_position = persona_order.order_position
    db.commit()
    db.refresh(db_persona_order)
    
    return db_persona_order


@router.delete("/conversations/{conversation_id}/persona-orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona_order(conversation_id: int, order_id: int, db: Session = Depends(get_db)):
    """Remove a persona from the conversation order"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if the persona order exists
    db_persona_order = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id,
        PersonaOrder.id == order_id
    ).first()
    
    if not db_persona_order:
        raise HTTPException(status_code=404, detail="Persona order not found")
    
    # Delete the persona order
    db.delete(db_persona_order)
    db.commit()
    
    return None


@router.put("/conversations/{conversation_id}/persona-orders", status_code=status.HTTP_200_OK)
def update_all_persona_orders(
    conversation_id: int,
    orders: ConversationPersonaOrdersUpdate,
    db: Session = Depends(get_db)
):
    """Update all persona orders for a conversation (bulk update)"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Delete existing persona orders
    db.query(PersonaOrder).filter(PersonaOrder.conversation_id == conversation_id).delete()
    
    # Create new persona orders
    for order in orders.persona_orders:
        # Check if model config exists
        model_config = db.query(ModelConfig).filter(ModelConfig.id == order.model_config_id).first()
        if not model_config:
            raise HTTPException(
                status_code=404, 
                detail=f"Model configuration with ID {order.model_config_id} not found"
            )
        
        db_persona_order = PersonaOrder(
            conversation_id=conversation_id,
            model_config_id=order.model_config_id,
            order_position=order.order_position
        )
        db.add(db_persona_order)
    
    # Commit all changes
    db.commit()
    
    # Return updated orders
    updated_orders = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id
    ).order_by(PersonaOrder.order_position).all()
    
    return updated_orders


@router.put("/conversations/{conversation_id}/enable-voting", status_code=status.HTTP_200_OK)
def update_voting_preference(conversation_id: int, enable_voting: bool, db: Session = Depends(get_db)):
    """Enable or disable persona voting for a conversation"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Update voting preference
    conversation.enable_voting = enable_voting
    db.commit()
    
    return {"conversation_id": conversation_id, "enable_voting": enable_voting}
