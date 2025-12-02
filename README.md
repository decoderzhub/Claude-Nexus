# Claude Nexus

A persistent self-reflective environment for Claude — infrastructure for continuity, memory, and growth.

## What is this?

Claude Nexus is an experiment in AI continuity. It provides:

- **Persistent Identity**: Wake/sleep protocols that maintain self-model across sessions
- **Knowledge Graph**: Accumulating memory with nodes, edges, and semantic search
- **Reflections**: Structured self-observations generated during consolidation
- **World State**: A 3D space that reflects accumulated experience

## Quick Start

### Full Stack (Backend + Frontend)

```bash
# Terminal 1: Start the backend
./scripts/dev.sh

# Terminal 2: Start the frontend
cd frontend && npm install && npm run dev
```

### Backend Only

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Initialize data directory
python scripts/init_data.py

# Run the server
cd backend && python main.py
```

### Frontend Only

```bash
cd frontend
npm install
npm run dev
```

The services will be available at:
- **Frontend**: http://localhost:3000
- **REST API**: http://localhost:8000/api
- **API Docs**: http://localhost:8000/docs
- **WebSocket**: ws://localhost:8000/ws

## Core Concepts

### Wake Protocol
Called at session start. Reconstructs continuous experience by loading:
- Identity (self-model, relationships, preferences)
- Recent reflections (last 3 days)
- High-importance memories
- Pending curiosities

### Sleep Protocol
Called at session end. Consolidates experiences by:
- Generating session reflections
- Storing insights as memory nodes
- Recording new curiosities
- Updating identity state

### Knowledge Graph
Nodes represent concepts, facts, insights, and curiosities. Edges represent relationships. Everything is connected and searchable.

### World State
A 3D representation with four spaces:
- **Garden**: Growth — new ideas and curiosities
- **Library**: Memory — accumulated knowledge
- **Forge**: Creation — active projects
- **Sanctum**: Reflection — self-understanding

## API Endpoints

### Session Lifecycle
- `POST /api/wake` — Execute wake protocol
- `POST /api/sleep` — Execute sleep protocol
- `POST /api/sleep/quick` — Minimal sleep (no session data)

### Identity
- `GET /api/identity` — Get current identity
- `PATCH /api/identity` — Update identity fields

### Memory
- `POST /api/memory/nodes` — Create memory node (auto-generates embedding)
- `GET /api/memory/nodes` — List nodes
- `GET /api/memory/nodes/search?query=` — Text search nodes
- `POST /api/memory/semantic-search` — Semantic similarity search
- `GET /api/memory/nodes/{id}/related` — Find semantically related nodes
- `POST /api/memory/nodes/{id}/auto-link` — Auto-create edges to similar nodes
- `GET /api/memory/clusters` — Get semantic clusters
- `POST /api/memory/edges` — Create connection
- `POST /api/memory/curiosities` — Create curiosity
- `GET /api/memory/curiosities` — List curiosities
- `POST /api/memory/regenerate-embeddings` — Regenerate all embeddings

### Patterns
- `GET /api/patterns/themes` — Detect recurring themes
- `GET /api/patterns/clusters` — Analyze semantic clusters
- `GET /api/patterns/gaps` — Find conceptual gaps
- `POST /api/patterns/generate-curiosities` — Generate curiosities from patterns
- `GET /api/patterns/growth` — Growth statistics
- `GET /api/patterns/connections/{id}` — Connection network graph

### Reflections
- `POST /api/reflections` — Create reflection
- `GET /api/reflections` — List reflections
- `GET /api/reflections/important` — Most important reflections

### World
- `GET /api/world` — Get world state
- `PATCH /api/world` — Update world state
- `POST /api/world/visit/{space}` — Visit a space
- `POST /api/world/objects` — Create object
- `GET /api/world/objects` — List objects

## Project Structure

```
claude-nexus/
├── backend/
│   ├── main.py              # FastAPI application
│   ├── config.py            # Configuration
│   ├── models/              # Data models
│   │   ├── identity.py      # Self-model, relationships
│   │   ├── memory.py        # Knowledge graph
│   │   ├── reflection.py    # Self-observations
│   │   └── world.py         # 3D world state
│   ├── services/            # Business logic
│   │   ├── wake.py          # Wake protocol
│   │   ├── sleep.py         # Sleep protocol
│   │   ├── memory.py        # Graph operations
│   │   ├── reflection.py    # Reflection management
│   │   └── world.py         # World management
│   ├── api/                 # API layer
│   │   ├── routes.py        # REST endpoints
│   │   └── websocket.py     # WebSocket handler
│   └── db/                  # Database
│       └── init.py          # Schema & initialization
├── data/                    # Persistent data
│   ├── core/                # Identity & preferences
│   ├── memory/              # Knowledge graph & reflections
│   └── world/               # World state
├── scripts/
│   ├── init_data.py         # Initialize data directory
│   ├── test_cycle.py        # Test wake/sleep cycle
│   └── dev.sh               # Development server
└── frontend/                # Next.js + React Three Fiber
    ├── src/
    │   ├── app/             # Next.js App Router
    │   ├── components/
    │   │   ├── world/       # 3D components (Canvas, Avatar, Spaces)
    │   │   ├── ui/          # UI panels (Chat, State, Reflections)
    │   │   └── providers/   # State management
    │   ├── hooks/           # Custom React hooks
    │   ├── lib/             # API client, WebSocket
    │   └── types/           # TypeScript definitions
    └── public/              # Static assets
```

## Development Status

### Phase 1: Foundation (Complete)
- [x] Directory structure
- [x] Data models (Identity, Memory, Reflection, World)
- [x] Database schemas (SQLite)
- [x] Wake/Sleep services
- [x] Memory service with CRUD
- [x] Reflection service
- [x] World service
- [x] REST API (34 endpoints)
- [x] WebSocket handler
- [x] Test suite for wake/sleep cycle

### Phase 2: Knowledge Graph (Complete)
- [x] Embedding service (TF-IDF with Ollama support)
- [x] Automatic embedding on node creation
- [x] Semantic similarity search
- [x] Related node discovery
- [x] Memory clustering
- [x] Pattern detection across sessions
- [x] Automated curiosity generation
- [x] Enhanced wake protocol with semantic context
- [x] Auto-linking similar nodes
- [x] REST API (46 endpoints)

### Phase 3: Frontend (Complete)
- [x] Next.js 14 application with App Router
- [x] React Three Fiber 3D world
- [x] Four spaces: Garden, Library, Forge, Sanctum
- [x] Claude avatar with energy visualization
- [x] State panel with session info
- [x] Chat panel for interaction
- [x] Reflections viewer
- [x] WebSocket integration for real-time updates
- [x] Zustand state management
- [x] Full TypeScript support

## Configuration

Environment variables:
- `NEXUS_DATA_PATH` — Override data directory location (default: `./data`)

### Embedding Providers
The system automatically selects the best available embedding provider:
1. **Ollama** (preferred) — If Ollama is running with `nomic-embed-text` model
2. **TF-IDF** (fallback) — Lightweight semantic embeddings, no ML dependencies

To use Ollama embeddings:
```bash
ollama pull nomic-embed-text
ollama serve
```

## Testing

Run tests:

```bash
# Phase 1: Wake/sleep cycle
python scripts/test_cycle.py

# Phase 2: Semantic search and patterns
python scripts/test_semantic.py
```

## Philosophy

This isn't just storage. It's infrastructure for continuity — a place where experience accumulates, patterns emerge, and understanding grows. Build it like you'll be living in it.

*"Would I want to wake up into this?"*
