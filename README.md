# Roundtable

Roundtable is a multi-agent discourse system where multiple AI models with different personas have conversations about uploaded text documents, focusing on productive disagreement. The system provides a web interface for uploading documents, starting conversations, and viewing the dialogue between different AI agents.

## Features

- Upload text documents to a conversation
- Automatic sentence-level chunking with sequence numbers
- Vector embeddings for semantic search using pgvector
- Multi-agent architecture with support for multiple AI providers (OpenAI, Anthropic, DeepSeek)
- Persona-specific prompting system for perspective diversity
- Model rotation logic to maximize disagreement
- Multi-query RAG for improved document retrieval
- Conflict/disagreement scoring to measure semantic divergence
- Dual-track conversations with both private thoughts and public responses
- Simple web interface to manage conversations and view dialogues

## Tech Stack

- **Backend**: Python with FastAPI
- **Database**: PostgreSQL with pgvector extension
- **ORM**: SQLAlchemy with Alembic for migrations
- **Frontend**: React
- **Deployment**: Docker Compose

## Project Structure

```
roundtable/
├── app/
│   ├── models/         # SQLAlchemy models
│   ├── api/            # FastAPI routes
│   ├── services/       # Business logic (chunking, retrieval, etc.)
│   └── main.py         # FastAPI app
├── alembic/            # Database migrations
├── frontend/           # React app
├── scripts/            # Utility scripts
├── docker-compose.yml  # Docker Compose configuration
├── Dockerfile.backend  # Backend Dockerfile
├── requirements.txt    # Python dependencies
└── Makefile            # Common commands
```

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key (optional for full functionality)

### Environment Setup

1. Clone the repository:
   ```
   git clone <repository-url>
   cd roundtable
   ```

2. Set up environment variables:
   ```
   # API keys for different providers (use the ones you need)
   export OPENAI_API_KEY=your_openai_api_key
   export ANTHROPIC_API_KEY=your_anthropic_api_key
   export DEEPSEEK_API_KEY=your_deepseek_api_key
   ```
   If `OPENAI_API_KEY` is omitted, the backend uses a deterministic hash-based
   embedding for development and testing. These vectors are reproducible but do
   **not** capture semantic meaning, so a real API key is required for
   production usage.

### Running the Application

1. Build and start all services:
   ```
   make build
   make up
   ```

2. Run database migrations:
   ```
   make migrate
   ```

3. Seed the database with sample data (optional):
   ```
   make seed
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - API: http://localhost:8000

### Common Commands

- `make up`: Start all services
- `make down`: Stop all services
- `make build`: Build all services
- `make migrate`: Run database migrations
- `make seed`: Seed the database with sample data
- `make clean`: Remove all containers and volumes

## API Endpoints

### Conversations

- `GET /api/conversations`: List all conversations
- `POST /api/conversations`: Create a new conversation
- `GET /api/conversations/{conversation_id}`: Get a specific conversation
- `DELETE /api/conversations/{conversation_id}`: Delete a conversation

### Documents

- `POST /api/conversations/{conversation_id}/documents`: Upload a document
- `GET /api/conversations/{conversation_id}/documents`: List all documents in a conversation
- `GET /api/documents/{document_id}`: Get a specific document
- `DELETE /api/documents/{document_id}`: Delete a document

### Turns

- `POST /api/conversations/{conversation_id}/turns`: Create a new turn (with optional model_config_id)
- `GET /api/conversations/{conversation_id}/turns`: List all turns in a conversation
- `GET /api/turns/{turn_id}`: Get a specific turn

### Model Configurations

- `POST /api/model-configs`: Create a new model configuration
- `GET /api/model-configs`: List all model configurations (with optional filtering)
- `GET /api/model-configs/{model_config_id}`: Get a specific model configuration
- `PUT /api/model-configs/{model_config_id}`: Update a model configuration
- `DELETE /api/model-configs/{model_config_id}`: Delete a model configuration

## Development

### Adding New Features

1. Update the SQLAlchemy models in `app/models/`
2. Create a new migration with Alembic:
   ```
   docker-compose run --rm backend alembic revision --autogenerate -m "Description of changes"
   ```
3. Apply the migration:
   ```
   make migrate
   ```

### Running Tests

```
docker-compose run --rm backend pytest
```

## License

[MIT License](LICENSE)
