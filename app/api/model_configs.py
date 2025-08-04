from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from app.db import get_db
from app.models import ModelConfig
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class ModelConfigBase(BaseModel):
    name: str
    provider: str
    model_id: str
    persona_name: str
    persona_description: str
    persona_instructions: str
    temperature: float = 0.7
    max_tokens: int = 500
    top_p: float = 1.0
    provider_parameters: Optional[dict] = None
    is_active: bool = True


class ModelConfigCreate(ModelConfigBase):
    pass


class ModelConfigUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    model_id: Optional[str] = None
    persona_name: Optional[str] = None
    persona_description: Optional[str] = None
    persona_instructions: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    top_p: Optional[float] = None
    provider_parameters: Optional[dict] = None
    is_active: Optional[bool] = None


class ModelConfigResponse(ModelConfigBase):
    id: int
    created_at: datetime

    class Config:
        orm_mode = True


@router.post("/model-configs", response_model=ModelConfigResponse, status_code=status.HTTP_201_CREATED)
def create_model_config(model_config: ModelConfigCreate, db: Session = Depends(get_db)):
    """Create a new model configuration"""
    # Convert provider_parameters to JSON string if provided
    provider_params = json.dumps(model_config.provider_parameters) if model_config.provider_parameters else None
    
    db_model_config = ModelConfig(
        name=model_config.name,
        provider=model_config.provider,
        model_id=model_config.model_id,
        persona_name=model_config.persona_name,
        persona_description=model_config.persona_description,
        persona_instructions=model_config.persona_instructions,
        temperature=model_config.temperature,
        max_tokens=model_config.max_tokens,
        top_p=model_config.top_p,
        provider_parameters=provider_params,
        is_active=model_config.is_active
    )
    
    db.add(db_model_config)
    db.commit()
    db.refresh(db_model_config)
    
    return db_model_config


@router.get("/model-configs", response_model=List[ModelConfigResponse])
def list_model_configs(
    active_only: bool = False,
    provider: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all model configurations with optional filtering"""
    query = db.query(ModelConfig)
    
    if active_only:
        query = query.filter(ModelConfig.is_active)
    
    if provider:
        query = query.filter(ModelConfig.provider == provider)
    
    model_configs = query.all()
    
    # Parse provider_parameters JSON for each model config
    for model_config in model_configs:
        if model_config.provider_parameters:
            try:
                model_config.provider_parameters = json.loads(model_config.provider_parameters)
            except json.JSONDecodeError:
                model_config.provider_parameters = {}
        else:
            model_config.provider_parameters = {}
    
    return model_configs


@router.get("/model-configs/{model_config_id}", response_model=ModelConfigResponse)
def get_model_config(model_config_id: int, db: Session = Depends(get_db)):
    """Get a specific model configuration by ID"""
    model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()
    if model_config is None:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    # Parse provider_parameters JSON
    if model_config.provider_parameters:
        try:
            model_config.provider_parameters = json.loads(model_config.provider_parameters)
        except json.JSONDecodeError:
            model_config.provider_parameters = {}
    else:
        model_config.provider_parameters = {}
    
    return model_config


@router.put("/model-configs/{model_config_id}", response_model=ModelConfigResponse)
def update_model_config(
    model_config_id: int,
    model_config_update: ModelConfigUpdate,
    db: Session = Depends(get_db)
):
    """Update a model configuration"""
    db_model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()
    if db_model_config is None:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    # Update model config fields if provided in the request
    update_data = model_config_update.dict(exclude_unset=True)
    
    # Handle provider_parameters separately to convert to JSON string
    if "provider_parameters" in update_data:
        provider_params = update_data.pop("provider_parameters")
        if provider_params is not None:
            db_model_config.provider_parameters = json.dumps(provider_params)
    
    # Update other fields
    for key, value in update_data.items():
        setattr(db_model_config, key, value)
    
    db.commit()
    db.refresh(db_model_config)
    
    return db_model_config


@router.delete("/model-configs/{model_config_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_model_config(model_config_id: int, db: Session = Depends(get_db)):
    """Delete a model configuration"""
    db_model_config = db.query(ModelConfig).filter(ModelConfig.id == model_config_id).first()
    if db_model_config is None:
        raise HTTPException(status_code=404, detail="Model configuration not found")
    
    db.delete(db_model_config)
    db.commit()
    
    return None
