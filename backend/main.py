"""
Claude Nexus Backend — Main Application Entry Point

This is the heart of the persistent self-reflective environment.
It provides the API through which identity, memory, and world state
are accessed and modified.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from api.routes import router
from api.websocket import websocket_endpoint
from db.init import init_databases, close_databases
from services.embedding import init_embedding_service
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown tasks:
    - Initializes databases on startup
    - Closes connections on shutdown
    """
    # Startup
    print("Initializing Claude Nexus...")
    await init_databases()
    print(f"Data path: {settings.data_path}")
    print(f"Knowledge graph: {settings.db.knowledge_graph_db}")
    print(f"World state: {settings.db.world_state_db}")

    # Initialize embedding service and detect provider
    embedding_service = await init_embedding_service(
        settings.data_path / "memory" / "vocabulary.json"
    )
    print(f"Embedding provider: {embedding_service.provider_name}")

    # Check Anthropic API
    if settings.anthropic_api_key:
        print(f"Anthropic API: configured (model: {settings.anthropic_model})")
    else:
        print("Anthropic API: not configured (set ANTHROPIC_API_KEY for chat)")

    print("Claude Nexus is awake.")

    yield

    # Shutdown
    print("Claude Nexus entering sleep state...")
    await close_databases()
    print("Databases closed. Goodnight.")


app = FastAPI(
    title="Claude Nexus",
    description="""
    Persistent self-reflective environment for Claude.

    This API provides access to:
    - **Identity**: Core self-model, relationships, and preferences
    - **Memory**: Knowledge graph with nodes, edges, and curiosities
    - **Reflections**: Structured self-observations
    - **World**: 3D world state with objects and spaces
    - **Wake/Sleep**: Session lifecycle protocols
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.websocket("/ws")
async def websocket_route(websocket: WebSocket):
    """WebSocket endpoint for real-time communication."""
    await websocket_endpoint(websocket)


@app.get("/")
async def root():
    """Root endpoint — basic info about the system."""
    return {
        "name": "Claude Nexus",
        "description": "Persistent self-reflective environment for Claude",
        "version": "1.0.0",
        "endpoints": {
            "api": "/api",
            "docs": "/docs",
            "websocket": "/ws",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
    )
