import sys
import types
import pathlib
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Ensure project root is on sys.path
ROOT_DIR = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Use SQLite for tests to avoid requiring PostgreSQL driver
os.environ.setdefault("DATABASE_URL", "sqlite://")

import app  # noqa: F401

# Stub heavy services before importing the FastAPI app
stub_document_processor = types.ModuleType("document_processor")

async def process_document(document_id: int, db):
    return 0

stub_document_processor.process_document = process_document
sys.modules["app.services.document_processor"] = stub_document_processor

stub_agent_service = types.ModuleType("agent_service")

async def generate_turn_response(conversation_id: int, turn_number: int, query=None, db=None, model_config_id=None):
    return "test response", "test thoughts"

stub_agent_service.generate_turn_response = generate_turn_response
sys.modules["app.services.agent_service"] = stub_agent_service

from app.db import get_db
from app.models.base import Base
from app.main import app

# Set up test database (SQLite in-memory)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)

# Dependency override
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

import pytest

@pytest.fixture()
def client():
    with TestClient(app) as c:
        yield c
