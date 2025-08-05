from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import API routers
from app.api import conversations, documents, turns, model_configs, persona_orders, persona_votes

# Create FastAPI app
app = FastAPI(
    title="Roundtable",
    description="A multi-agent discourse system",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversations.router, prefix="/api", tags=["conversations"])
app.include_router(documents.router, prefix="/api", tags=["documents"])
app.include_router(turns.router, prefix="/api", tags=["turns"])
app.include_router(model_configs.router, prefix="/api", tags=["model_configs"])
app.include_router(persona_orders.router, prefix="/api", tags=["persona_orders"])
app.include_router(persona_votes.router, prefix="/api", tags=["persona_votes"])

# Mount static files for frontend
# app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}
