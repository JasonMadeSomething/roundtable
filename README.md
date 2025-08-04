# Roundtable

Roundtable is a multi-agent discourse system where a single model (OpenAI GPT) has a conversation with itself about uploaded text documents. The system provides a simple web interface for uploading documents, starting conversations, and viewing the dialogue.

## Features

- Upload text documents to a conversation
- Automatic sentence-level chunking with sequence numbers
- Vector embeddings for semantic search using pgvector
- Turn-based conversation system where the model responds to its own previous responses
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
   export OPENAI_API_KEY=your_openai_api_key  # Optional but recommended
   ```

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

- `POST /api/conversations/{conversation_id}/turns`: Create a new turn
- `GET /api/conversations/{conversation_id}/turns`: List all turns in a conversation
- `GET /api/turns/{turn_id}`: Get a specific turn

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
