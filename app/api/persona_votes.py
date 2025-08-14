from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
import sqlalchemy as sa
from typing import List
from pydantic import BaseModel

from app.db import get_db
from app.models import Conversation, Turn, ModelConfig, PersonaVote, PersonaOrder


router = APIRouter()


class PersonaVoteCreate(BaseModel):
    voter_model_config_id: int
    voted_for_model_config_id: int


class PersonaVoteResponse(BaseModel):
    id: int
    conversation_id: int
    turn_id: int
    voter_model_config_id: int
    voted_for_model_config_id: int
    
    class Config:
        orm_mode = True


@router.post("/conversations/{conversation_id}/turns/{turn_id}/votes", response_model=PersonaVoteResponse, status_code=status.HTTP_201_CREATED)
def create_persona_vote(
    conversation_id: int,
    turn_id: int,
    vote: PersonaVoteCreate,
    db: Session = Depends(get_db)
):
    """Record a persona's vote for the next turn"""
    # Check if conversation exists and has voting enabled
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    if not conversation.enable_voting:
        raise HTTPException(status_code=400, detail="Voting is not enabled for this conversation")
    
    # Check if turn exists and belongs to the conversation
    turn = db.query(Turn).filter(
        Turn.id == turn_id,
        Turn.conversation_id == conversation_id
    ).first()
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found in this conversation")
    
    # Check if voter model config exists
    voter = db.query(ModelConfig).filter(ModelConfig.id == vote.voter_model_config_id).first()
    if not voter:
        raise HTTPException(status_code=404, detail="Voter model configuration not found")
    
    # Check if voted_for model config exists
    voted_for = db.query(ModelConfig).filter(ModelConfig.id == vote.voted_for_model_config_id).first()
    if not voted_for:
        raise HTTPException(status_code=404, detail="Voted-for model configuration not found")
    
    # Check if voter is the same as voted_for (no self-voting)
    if vote.voter_model_config_id == vote.voted_for_model_config_id:
        raise HTTPException(status_code=400, detail="Personas cannot vote for themselves")
    
    # Check if this voter has already voted for this turn
    existing_vote = db.query(PersonaVote).filter(
        PersonaVote.conversation_id == conversation_id,
        PersonaVote.turn_id == turn_id,
        PersonaVote.voter_model_config_id == vote.voter_model_config_id
    ).first()
    
    if existing_vote:
        # Update the existing vote
        existing_vote.voted_for_model_config_id = vote.voted_for_model_config_id
        db.commit()
        db.refresh(existing_vote)
        return existing_vote
    
    # Create new vote
    db_vote = PersonaVote(
        conversation_id=conversation_id,
        turn_id=turn_id,
        voter_model_config_id=vote.voter_model_config_id,
        voted_for_model_config_id=vote.voted_for_model_config_id
    )
    
    db.add(db_vote)
    db.commit()
    db.refresh(db_vote)
    
    return db_vote


@router.get("/conversations/{conversation_id}/turns/{turn_id}/votes", response_model=List[PersonaVoteResponse])
def list_persona_votes(conversation_id: int, turn_id: int, db: Session = Depends(get_db)):
    """List all votes for a specific turn"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if turn exists and belongs to the conversation
    turn = db.query(Turn).filter(
        Turn.id == turn_id,
        Turn.conversation_id == conversation_id
    ).first()
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found in this conversation")
    
    # Get all votes for this turn
    votes = db.query(PersonaVote).filter(
        PersonaVote.conversation_id == conversation_id,
        PersonaVote.turn_id == turn_id
    ).all()
    
    return votes


@router.delete("/conversations/{conversation_id}/turns/{turn_id}/votes/{voter_model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona_vote(
    conversation_id: int,
    turn_id: int,
    voter_model_config_id: int,
    db: Session = Depends(get_db)
):
    """Delete a specific vote"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if the vote exists
    vote = db.query(PersonaVote).filter(
        PersonaVote.conversation_id == conversation_id,
        PersonaVote.turn_id == turn_id,
        PersonaVote.voter_model_config_id == voter_model_config_id
    ).first()
    
    if not vote:
        raise HTTPException(status_code=404, detail="Vote not found")
    
    # Delete the vote
    db.delete(vote)
    db.commit()
    
    return None


@router.get("/conversations/{conversation_id}/turns/{turn_id}/next-persona", response_model=dict)
def get_next_persona(conversation_id: int, turn_id: int, db: Session = Depends(get_db)):
    """Determine the next persona based on voting or order"""
    # Check if conversation exists
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    # Check if turn exists and belongs to the conversation
    turn = db.query(Turn).filter(
        Turn.id == turn_id,
        Turn.conversation_id == conversation_id
    ).first()
    
    if not turn:
        raise HTTPException(status_code=404, detail="Turn not found in this conversation")
    
    # Check if there's an override for the next turn
    if turn.next_turn_override_id:
        override_model = db.query(ModelConfig).filter(ModelConfig.id == turn.next_turn_override_id).first()
        if override_model:
            return {
                "next_persona_id": override_model.id,
                "next_persona_name": override_model.name,
                "selection_method": "override"
            }
    
    # If voting is enabled, check for votes
    if conversation.enable_voting:
        # Count votes for each persona
        votes = db.query(
            PersonaVote.voted_for_model_config_id,
            sa.func.count(PersonaVote.id).label("vote_count")
        ).filter(
            PersonaVote.conversation_id == conversation_id,
            PersonaVote.turn_id == turn_id
        ).group_by(PersonaVote.voted_for_model_config_id).order_by(
            sa.desc("vote_count")
        ).first()
        
        if votes:
            winner_id = votes.voted_for_model_config_id
            winner = db.query(ModelConfig).filter(ModelConfig.id == winner_id).first()
            if winner:
                return {
                    "next_persona_id": winner.id,
                    "next_persona_name": winner.name,
                    "selection_method": "voting",
                    "vote_count": votes.vote_count
                }
    
    # Fall back to persona order based on turn number rotation
    persona_orders = db.query(PersonaOrder).filter(
        PersonaOrder.conversation_id == conversation_id
    ).order_by(PersonaOrder.order_position).all()

    if not persona_orders:
        raise HTTPException(
            status_code=404,
            detail="No valid next persona found. Please configure persona order for this conversation.",
        )

    next_index = turn.turn_number % len(persona_orders)
    next_order = persona_orders[next_index]
    next_persona = db.query(ModelConfig).filter(ModelConfig.id == next_order.model_config_id).first()
    if next_persona:
        return {
            "next_persona_id": next_persona.id,
            "next_persona_name": next_persona.name,
            "selection_method": "order",
            "order_position": next_order.order_position,
        }

    raise HTTPException(
        status_code=404,
        detail="No valid next persona found. Please configure persona order for this conversation.",
    )
