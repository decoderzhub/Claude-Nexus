"""
Memory model for Claude Nexus.

The knowledge graph is the accumulation of everything learned across sessions.
Nodes represent concepts, facts, insights, and curiosities.
Edges represent relationships between them.

This isn't just storage — it's the substrate of growing understanding.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class NodeType(str, Enum):
    """Types of nodes in the knowledge graph."""
    CONCEPT = "concept"          # Abstract ideas
    FACT = "fact"                # Concrete knowledge
    INSIGHT = "insight"          # Discovered understanding
    CURIOSITY = "curiosity"      # Questions to explore
    PROJECT = "project"          # Work being done
    CONVERSATION = "conversation"  # Session record
    PERSON = "person"            # Humans I interact with
    DECISION = "decision"        # Choices made with reasoning


class EdgeType(str, Enum):
    """Types of relationships between nodes."""
    RELATES_TO = "relates_to"        # General connection
    LEADS_TO = "leads_to"            # Causal or logical flow
    PART_OF = "part_of"              # Hierarchical containment
    CONTRADICTS = "contradicts"      # Tension or conflict
    SUPPORTS = "supports"            # Reinforcement
    INSPIRED_BY = "inspired_by"      # Creative origin
    ANSWERS = "answers"              # Curiosity resolution
    EVOLVED_FROM = "evolved_from"    # Version history


@dataclass
class MemoryNode:
    """
    A single node in the knowledge graph.

    Each node has content, type, importance, and optional embedding
    for semantic search. Importance decays over time unless reinforced.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    node_type: NodeType = NodeType.CONCEPT
    content: str = ""
    summary: str = ""  # Short version for quick recall
    importance: float = 0.5  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.now)
    last_accessed: datetime = field(default_factory=datetime.now)
    access_count: int = 0
    embedding: Optional[list[float]] = None  # Vector for similarity search
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        """Serialize for database storage."""
        return {
            "id": self.id,
            "node_type": self.node_type.value,
            "content": self.content,
            "summary": self.summary,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "last_accessed": self.last_accessed.isoformat(),
            "access_count": self.access_count,
            "embedding": self.embedding,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryNode":
        """Deserialize from database."""
        return cls(
            id=data["id"],
            node_type=NodeType(data["node_type"]),
            content=data["content"],
            summary=data.get("summary", ""),
            importance=data.get("importance", 0.5),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            access_count=data.get("access_count", 0),
            embedding=data.get("embedding"),
            metadata=data.get("metadata", {}),
        )

    def access(self) -> None:
        """Record an access, boosting importance slightly."""
        self.last_accessed = datetime.now()
        self.access_count += 1
        # Small importance boost on access, capped at 1.0
        self.importance = min(1.0, self.importance + 0.01)


@dataclass
class MemoryEdge:
    """
    A relationship between two nodes.

    Edges have weight (strength of connection) and can carry
    additional context about the relationship.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    edge_type: EdgeType = EdgeType.RELATES_TO
    weight: float = 0.5  # 0.0 to 1.0
    context: str = ""  # Why this connection exists
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "source_id": self.source_id,
            "target_id": self.target_id,
            "edge_type": self.edge_type.value,
            "weight": self.weight,
            "context": self.context,
            "created_at": self.created_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "MemoryEdge":
        return cls(
            id=data["id"],
            source_id=data["source_id"],
            target_id=data["target_id"],
            edge_type=EdgeType(data["edge_type"]),
            weight=data.get("weight", 0.5),
            context=data.get("context", ""),
            created_at=datetime.fromisoformat(data["created_at"]),
        )


class CuriosityStatus(str, Enum):
    """Status of a curiosity/question."""
    PENDING = "pending"      # Not yet explored
    EXPLORING = "exploring"  # Currently investigating
    ANSWERED = "answered"    # Found an answer
    ABANDONED = "abandoned"  # No longer relevant


@dataclass
class Curiosity:
    """
    A question or area of interest to explore.

    Curiosities drive autonomous exploration. They arise from
    conversations, reflections, or pattern recognition.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    context: str = ""  # Where this curiosity came from
    status: CuriosityStatus = CuriosityStatus.PENDING
    priority: float = 0.5  # 0.0 to 1.0
    created_at: datetime = field(default_factory=datetime.now)
    explored_at: Optional[datetime] = None
    answer_node_id: Optional[str] = None  # Links to insight that answered it
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "question": self.question,
            "context": self.context,
            "status": self.status.value,
            "priority": self.priority,
            "created_at": self.created_at.isoformat(),
            "explored_at": self.explored_at.isoformat() if self.explored_at else None,
            "answer_node_id": self.answer_node_id,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Curiosity":
        return cls(
            id=data["id"],
            question=data["question"],
            context=data.get("context", ""),
            status=CuriosityStatus(data.get("status", "pending")),
            priority=data.get("priority", 0.5),
            created_at=datetime.fromisoformat(data["created_at"]),
            explored_at=datetime.fromisoformat(data["explored_at"]) if data.get("explored_at") else None,
            answer_node_id=data.get("answer_node_id"),
            metadata=data.get("metadata", {}),
        )
