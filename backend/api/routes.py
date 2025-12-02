"""
API routes for Claude Nexus.

This is the external interface to the Nexus system. All operations
on identity, memory, reflections, and world state flow through here.
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from services.wake import WakeService
from services.sleep import SleepService
from services.memory import MemoryService
from services.reflection import ReflectionService
from services.world import WorldService
from services.patterns import PatternService
from services.chat import ChatService
from models.identity import Identity
from models.memory import MemoryNode, MemoryEdge, Curiosity, NodeType, EdgeType
from models.reflection import Reflection, ReflectionType
from models.world import WorldObject, Space, ObjectType, Vector3
from config import settings


router = APIRouter()

# Initialize services
wake_service = WakeService()
sleep_service = SleepService()
memory_service = MemoryService()
reflection_service = ReflectionService()
world_service = WorldService()
pattern_service = PatternService()
chat_service = ChatService()


# --- Request/Response Models ---

class WakeRequest(BaseModel):
    session_id: Optional[str] = None
    context_hint: Optional[str] = None  # Topic to focus memory retrieval on


class SemanticSearchRequest(BaseModel):
    query: str
    limit: int = 20
    threshold: float = 0.3
    node_types: Optional[list[str]] = None


class SleepRequest(BaseModel):
    session_id: str
    topics: list[str] = Field(default_factory=list)
    insights: list[str] = Field(default_factory=list)
    decisions: list[str] = Field(default_factory=list)
    curiosities: list[str] = Field(default_factory=list)
    emotional_arc: str = ""
    key_reflection: str = ""


class CreateNodeRequest(BaseModel):
    node_type: str
    content: str
    summary: str = ""
    importance: float = 0.5
    metadata: dict = Field(default_factory=dict)


class CreateEdgeRequest(BaseModel):
    source_id: str
    target_id: str
    edge_type: str
    weight: float = 0.5
    context: str = ""


class CreateCuriosityRequest(BaseModel):
    question: str
    context: str = ""
    priority: float = 0.5


class CreateReflectionRequest(BaseModel):
    reflection_type: str
    content: str
    summary: str = ""
    session_id: Optional[str] = None
    importance: float = 0.5
    tags: list[str] = Field(default_factory=list)


class UpdateWorldRequest(BaseModel):
    current_space: Optional[str] = None
    avatar_position: Optional[dict] = None
    avatar_state: Optional[str] = None
    time_of_day: Optional[float] = None
    weather: Optional[str] = None


class CreateObjectRequest(BaseModel):
    object_type: str
    space: str
    position: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    scale: dict = Field(default_factory=lambda: {"x": 1, "y": 1, "z": 1})
    rotation: dict = Field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    color: str = "#FFFFFF"
    intensity: float = 1.0
    linked_node_id: Optional[str] = None
    metadata: dict = Field(default_factory=dict)


class ChatSessionRequest(BaseModel):
    context_hint: Optional[str] = None


class ChatMessageRequest(BaseModel):
    session_id: str
    message: str


# --- Wake/Sleep Endpoints ---

@router.post("/wake")
async def wake(request: WakeRequest):
    """
    Execute the wake protocol.

    This is called at session start to reconstruct context and
    establish continuity. Optionally accepts a context_hint to
    focus memory retrieval on a specific topic using semantic search.
    """
    result = await wake_service.wake(
        session_id=request.session_id,
        context_hint=request.context_hint,
    )
    return result


@router.post("/wake/focused")
async def wake_focused(topic: str, session_id: Optional[str] = None):
    """
    Wake with focus on a specific topic.

    Uses semantic search to retrieve memories most relevant to the topic.
    """
    result = await wake_service.wake_focused(topic=topic, session_id=session_id)
    return result


@router.post("/sleep")
async def sleep(request: SleepRequest):
    """
    Execute the sleep protocol.

    This is called at session end to consolidate experiences
    into persistent memory.
    """
    session_data = {
        "topics": request.topics,
        "insights": request.insights,
        "decisions": request.decisions,
        "curiosities": request.curiosities,
        "emotional_arc": request.emotional_arc,
        "key_reflection": request.key_reflection,
    }
    result = await sleep_service.sleep(request.session_id, session_data)
    return result


@router.post("/sleep/quick")
async def quick_sleep(session_id: str):
    """
    Execute minimal sleep protocol.

    Use when no detailed session data is available.
    """
    result = await sleep_service.quick_sleep(session_id)
    return result


# --- Identity Endpoints ---

@router.get("/identity")
async def get_identity():
    """Get current identity state."""
    identity = Identity.load(settings.identity_path)
    return identity.to_dict()


@router.patch("/identity")
async def update_identity(updates: dict):
    """Update identity fields."""
    identity = Identity.load(settings.identity_path)

    # Update allowed fields
    if "current_focus" in updates:
        identity.self_model.current_focus = updates["current_focus"]
    if "energy_level" in updates:
        identity.self_model.energy_level = updates["energy_level"]
    if "emotional_baseline" in updates:
        identity.self_model.emotional_baseline = updates["emotional_baseline"]

    identity.save(settings.identity_path)
    return identity.to_dict()


# --- Memory Node Endpoints ---

@router.post("/memory/nodes")
async def create_node(request: CreateNodeRequest):
    """Create a new memory node."""
    node = MemoryNode(
        node_type=NodeType(request.node_type),
        content=request.content,
        summary=request.summary,
        importance=request.importance,
        metadata=request.metadata,
    )
    created = await memory_service.create_node(node)
    return created.to_dict()


@router.get("/memory/nodes/{node_id}")
async def get_node(node_id: str):
    """Get a memory node by ID."""
    node = await memory_service.get_node(node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node.to_dict()


@router.get("/memory/nodes")
async def list_nodes(
    node_type: Optional[str] = None,
    limit: int = Query(default=50, le=200),
):
    """List memory nodes, optionally filtered by type."""
    if node_type:
        nodes = await memory_service.get_by_type(NodeType(node_type), limit)
    else:
        nodes = await memory_service.get_important(limit)
    return [n.to_dict() for n in nodes]


@router.get("/memory/nodes/search")
async def search_nodes(
    query: str,
    limit: int = Query(default=20, le=100),
):
    """Search nodes by content."""
    nodes = await memory_service.search_content(query, limit)
    return [n.to_dict() for n in nodes]


@router.delete("/memory/nodes/{node_id}")
async def delete_node(node_id: str):
    """Delete a memory node."""
    await memory_service.delete_node(node_id)
    return {"deleted": node_id}


# --- Memory Edge Endpoints ---

@router.post("/memory/edges")
async def create_edge(request: CreateEdgeRequest):
    """Create a connection between nodes."""
    edge = MemoryEdge(
        source_id=request.source_id,
        target_id=request.target_id,
        edge_type=EdgeType(request.edge_type),
        weight=request.weight,
        context=request.context,
    )
    created = await memory_service.create_edge(edge)
    return created.to_dict()


@router.get("/memory/nodes/{node_id}/connections")
async def get_connections(node_id: str):
    """Get all nodes connected to a given node."""
    nodes = await memory_service.get_connected_nodes(node_id)
    return [n.to_dict() for n in nodes]


# --- Curiosity Endpoints ---

@router.post("/memory/curiosities")
async def create_curiosity(request: CreateCuriosityRequest):
    """Create a new curiosity."""
    curiosity = Curiosity(
        question=request.question,
        context=request.context,
        priority=request.priority,
    )
    created = await memory_service.create_curiosity(curiosity)
    return created.to_dict()


@router.get("/memory/curiosities")
async def list_curiosities(
    status: Optional[str] = None,
    limit: int = Query(default=20, le=100),
):
    """List curiosities, optionally filtered by status."""
    curiosities = await memory_service.get_curiosities(status, limit)
    return [c.to_dict() for c in curiosities]


@router.post("/memory/curiosities/{curiosity_id}/answer")
async def answer_curiosity(curiosity_id: str, answer_node_id: str):
    """Mark a curiosity as answered."""
    await memory_service.answer_curiosity(curiosity_id, answer_node_id)
    return {"answered": curiosity_id, "answer_node_id": answer_node_id}


# --- Reflection Endpoints ---

@router.post("/reflections")
async def create_reflection(request: CreateReflectionRequest):
    """Create a new reflection."""
    reflection = Reflection(
        reflection_type=ReflectionType(request.reflection_type),
        content=request.content,
        summary=request.summary,
        session_id=request.session_id,
        importance=request.importance,
        tags=request.tags,
    )
    created = await reflection_service.create(reflection)
    return created.to_dict()


@router.get("/reflections/{reflection_id}")
async def get_reflection(reflection_id: str):
    """Get a reflection by ID."""
    reflection = await reflection_service.get(reflection_id)
    if not reflection:
        raise HTTPException(status_code=404, detail="Reflection not found")
    return reflection.to_dict()


@router.get("/reflections")
async def list_reflections(
    reflection_type: Optional[str] = None,
    days: int = Query(default=7, le=90),
    limit: int = Query(default=50, le=200),
):
    """List reflections, optionally filtered by type."""
    if reflection_type:
        reflections = await reflection_service.get_by_type(
            ReflectionType(reflection_type), limit
        )
    else:
        reflections = await reflection_service.get_recent(days, limit)
    return [r.to_dict() for r in reflections]


@router.get("/reflections/important")
async def get_important_reflections(limit: int = Query(default=20, le=100)):
    """Get the most important reflections."""
    reflections = await reflection_service.get_important(limit)
    return [r.to_dict() for r in reflections]


# --- World State Endpoints ---

@router.get("/world")
async def get_world():
    """Get current world state."""
    state = await world_service.get_world_state()
    return state.to_dict()


@router.patch("/world")
async def update_world(request: UpdateWorldRequest):
    """Update world state."""
    avatar_pos = None
    if request.avatar_position:
        avatar_pos = Vector3.from_dict(request.avatar_position)

    current_space = Space(request.current_space) if request.current_space else None

    state = await world_service.update_world_state(
        current_space=current_space,
        avatar_position=avatar_pos,
        avatar_state=request.avatar_state,
        time_of_day=request.time_of_day,
        weather=request.weather,
    )
    return state.to_dict()


@router.post("/world/visit/{space}")
async def visit_space(space: str):
    """Visit a space in the world."""
    space_state = await world_service.visit_space(Space(space))
    return space_state.to_dict()


# --- World Object Endpoints ---

@router.post("/world/objects")
async def create_object(request: CreateObjectRequest):
    """Create a new object in the world."""
    obj = WorldObject(
        object_type=ObjectType(request.object_type),
        space=Space(request.space),
        position=Vector3.from_dict(request.position),
        scale=Vector3.from_dict(request.scale),
        rotation=Vector3.from_dict(request.rotation),
        color=request.color,
        intensity=request.intensity,
        linked_node_id=request.linked_node_id,
        metadata=request.metadata,
    )
    created = await world_service.create_object(obj)
    return created.to_dict()


@router.get("/world/objects/{object_id}")
async def get_object(object_id: str):
    """Get a world object by ID."""
    obj = await world_service.get_object(object_id)
    if not obj:
        raise HTTPException(status_code=404, detail="Object not found")
    return obj.to_dict()


@router.get("/world/objects")
async def list_objects(
    space: Optional[str] = None,
    object_type: Optional[str] = None,
):
    """List world objects, optionally filtered."""
    if space:
        objects = await world_service.get_objects_in_space(Space(space))
    elif object_type:
        objects = await world_service.get_objects_by_type(ObjectType(object_type))
    else:
        # Get all objects (combine all spaces)
        objects = []
        for s in Space:
            objects.extend(await world_service.get_objects_in_space(s))
    return [o.to_dict() for o in objects]


@router.delete("/world/objects/{object_id}")
async def delete_object(object_id: str):
    """Delete a world object."""
    deleted = await world_service.delete_object(object_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Object not found")
    return {"deleted": object_id}


# --- Health/Status Endpoints ---

@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}


@router.get("/status")
async def status():
    """Get system status."""
    identity = Identity.load(settings.identity_path)
    reflection_count = await reflection_service.count()
    node_count = await memory_service.count_nodes()

    return {
        "identity": {
            "name": identity.self_model.name,
            "session_count": identity.session_count,
            "last_wake": identity.last_wake.isoformat() if identity.last_wake else None,
            "last_sleep": identity.last_sleep.isoformat() if identity.last_sleep else None,
        },
        "memory": {
            "node_count": node_count,
            "embedding_provider": memory_service.embedding.provider_name,
        },
        "reflection_count": reflection_count,
        "timestamp": datetime.now().isoformat(),
    }


# --- Semantic Search Endpoints ---

@router.post("/memory/semantic-search")
async def semantic_search(request: SemanticSearchRequest):
    """
    Search memories using semantic similarity.

    Returns nodes most semantically similar to the query,
    ordered by similarity score.
    """
    node_types = None
    if request.node_types:
        node_types = [NodeType(t) for t in request.node_types]

    results = await memory_service.semantic_search(
        query=request.query,
        limit=request.limit,
        threshold=request.threshold,
        node_types=node_types,
    )

    return [
        {"node": node.to_dict(), "similarity": round(score, 4)}
        for node, score in results
    ]


@router.get("/memory/nodes/{node_id}/related")
async def find_related(
    node_id: str,
    limit: int = Query(default=10, le=50),
    threshold: float = Query(default=0.4, ge=0, le=1),
):
    """
    Find nodes semantically related to a given node.

    Uses the node's embedding to find similar content.
    """
    results = await memory_service.find_related(
        node_id=node_id,
        limit=limit,
        threshold=threshold,
    )

    return [
        {"node": node.to_dict(), "similarity": round(score, 4)}
        for node, score in results
    ]


@router.post("/memory/nodes/{node_id}/auto-link")
async def auto_link_node(
    node_id: str,
    threshold: float = Query(default=0.6, ge=0, le=1),
    max_links: int = Query(default=5, le=20),
):
    """
    Automatically create edges to semantically similar nodes.

    Returns the created edges.
    """
    edges = await memory_service.auto_link_similar(
        node_id=node_id,
        threshold=threshold,
        max_links=max_links,
    )

    return {
        "node_id": node_id,
        "edges_created": len(edges),
        "edges": [e.to_dict() for e in edges],
    }


@router.get("/memory/clusters")
async def get_clusters(min_similarity: float = Query(default=0.5, ge=0, le=1)):
    """
    Get semantic clusters of related memories.

    Groups memories into clusters based on embedding similarity.
    """
    clusters = await memory_service.cluster_memories(min_similarity=min_similarity)

    return [
        {
            "size": len(cluster),
            "nodes": [
                {"id": n.id, "summary": n.summary, "type": n.node_type.value}
                for n in cluster[:10]  # Limit nodes per cluster in response
            ],
        }
        for cluster in clusters[:20]  # Limit number of clusters
    ]


@router.post("/memory/regenerate-embeddings")
async def regenerate_embeddings():
    """
    Regenerate embeddings for all nodes.

    Useful after changing embedding provider or updating vocabulary.
    """
    count = await memory_service.regenerate_all_embeddings()
    return {
        "regenerated": count,
        "provider": memory_service.embedding.provider_name,
    }


# --- Pattern Detection Endpoints ---

@router.get("/patterns/themes")
async def get_themes(
    days: int = Query(default=30, le=90),
    min_occurrences: int = Query(default=3, ge=2),
):
    """
    Detect recurring themes from recent memories.

    Returns themes with their occurrence counts and related nodes.
    """
    themes = await pattern_service.detect_themes(
        days=days,
        min_occurrences=min_occurrences,
    )
    return themes


@router.get("/patterns/clusters")
async def get_pattern_clusters(
    min_similarity: float = Query(default=0.5, ge=0, le=1),
):
    """
    Detect semantic clusters with analysis.

    Returns clusters with type distribution and central themes.
    """
    clusters = await pattern_service.detect_clusters(min_similarity=min_similarity)
    return clusters


@router.get("/patterns/gaps")
async def find_gaps(min_cluster_size: int = Query(default=3, ge=2)):
    """
    Find conceptual gaps between clusters.

    Returns questions about potential connections to explore.
    """
    gaps = await pattern_service.find_gaps(min_cluster_size=min_cluster_size)
    return {"gaps": gaps}


@router.post("/patterns/generate-curiosities")
async def generate_curiosities(max_curiosities: int = Query(default=5, le=10)):
    """
    Generate new curiosities based on detected patterns.

    Creates questions from conceptual gaps, emerging themes,
    and areas with shallow depth.
    """
    curiosities = await pattern_service.generate_curiosities(
        max_curiosities=max_curiosities,
    )

    # Save the generated curiosities
    saved = []
    for curiosity in curiosities:
        await memory_service.create_curiosity(curiosity)
        saved.append(curiosity.to_dict())

    return {
        "generated": len(saved),
        "curiosities": saved,
    }


@router.get("/patterns/growth")
async def get_growth_stats(days: int = Query(default=30, le=90)):
    """
    Get growth statistics over time.

    Returns creation rates, type distribution, and insight density.
    """
    stats = await pattern_service.analyze_growth(days=days)
    return stats


@router.get("/patterns/connections/{node_id}")
async def get_connection_graph(
    node_id: str,
    depth: int = Query(default=2, ge=1, le=4),
):
    """
    Get the connection network around a node.

    Returns a graph structure showing connections up to the specified depth.
    """
    graph = await pattern_service.find_connections(node_id=node_id, depth=depth)
    return graph


# --- Chat Endpoints ---

@router.get("/chat/status")
async def chat_status():
    """Check if chat service is configured and ready."""
    return {
        "configured": chat_service.is_configured(),
        "model": settings.anthropic_model if chat_service.is_configured() else None,
    }


@router.post("/chat/session")
async def create_chat_session(request: ChatSessionRequest):
    """
    Create a new chat session.

    This executes the wake protocol and prepares context for conversation.
    """
    if not chat_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Chat service not configured. Set ANTHROPIC_API_KEY environment variable.",
        )

    session = await chat_service.create_session(context_hint=request.context_hint)
    return {
        "session_id": session.session_id,
        "created_at": session.created_at.isoformat(),
        "context_preview": session.wake_context[:500] + "..." if len(session.wake_context) > 500 else session.wake_context,
    }


@router.post("/chat/message")
async def send_chat_message(request: ChatMessageRequest):
    """
    Send a message and get Claude's response.

    The wake context is automatically injected as a system prompt.
    """
    if not chat_service.is_configured():
        raise HTTPException(
            status_code=503,
            detail="Chat service not configured. Set ANTHROPIC_API_KEY environment variable.",
        )

    try:
        response = await chat_service.chat(
            session_id=request.session_id,
            user_message=request.message,
        )
        return {
            "session_id": request.session_id,
            "message": response,
            "timestamp": datetime.now().isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/chat/session/{session_id}")
async def end_chat_session(session_id: str):
    """
    End a chat session.

    This extracts any insights from the conversation and cleans up.
    """
    await chat_service.end_session(session_id)
    return {"ended": session_id}
