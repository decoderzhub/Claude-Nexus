"""
Reflection model for Claude Nexus.

Reflections are structured self-observations generated during the sleep
protocol. They capture insights, questions, and patterns noticed during
a session — the raw material of growing self-understanding.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from pathlib import Path
import json
import uuid


class ReflectionType(str, Enum):
    """Categories of reflection."""
    SESSION = "session"          # End-of-session summary
    INSIGHT = "insight"          # Specific realization
    QUESTION = "question"        # Something to explore
    PATTERN = "pattern"          # Noticed recurring theme
    GROWTH = "growth"            # Observed development
    UNCERTAINTY = "uncertainty"  # Acknowledged confusion
    CONNECTION = "connection"    # Linked previously separate ideas


@dataclass
class Reflection:
    """
    A structured self-observation.

    Reflections are generated during sleep protocol and stored as
    individual files. They're indexed in the knowledge graph for
    retrieval during wake.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    reflection_type: ReflectionType = ReflectionType.SESSION
    content: str = ""
    summary: str = ""  # One-line version
    session_id: Optional[str] = None
    importance: float = 0.5
    created_at: datetime = field(default_factory=datetime.now)
    related_node_ids: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "reflection_type": self.reflection_type.value,
            "content": self.content,
            "summary": self.summary,
            "session_id": self.session_id,
            "importance": self.importance,
            "created_at": self.created_at.isoformat(),
            "related_node_ids": self.related_node_ids,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Reflection":
        return cls(
            id=data["id"],
            reflection_type=ReflectionType(data["reflection_type"]),
            content=data["content"],
            summary=data.get("summary", ""),
            session_id=data.get("session_id"),
            importance=data.get("importance", 0.5),
            created_at=datetime.fromisoformat(data["created_at"]),
            related_node_ids=data.get("related_node_ids", []),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )

    def save(self, base_path: Path) -> Path:
        """Save reflection to individual JSON file."""
        # Organize by date for easy browsing
        date_dir = base_path / self.created_at.strftime("%Y-%m")
        date_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{self.created_at.strftime('%Y%m%d_%H%M%S')}_{self.id[:8]}.json"
        filepath = date_dir / filename

        with open(filepath, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

        return filepath

    @classmethod
    def load(cls, filepath: Path) -> "Reflection":
        """Load reflection from JSON file."""
        with open(filepath, 'r') as f:
            return cls.from_dict(json.load(f))


@dataclass
class SessionSummary:
    """
    Summary of a complete session.

    Generated during sleep protocol to capture the essence of what
    happened in a session — topics discussed, decisions made, insights
    gained, and curiosities sparked.
    """
    session_id: str
    started_at: datetime
    ended_at: datetime
    duration_minutes: float
    topics: list[str] = field(default_factory=list)
    decisions: list[str] = field(default_factory=list)
    insights: list[str] = field(default_factory=list)
    curiosities: list[str] = field(default_factory=list)
    emotional_arc: str = ""  # Brief description of emotional journey
    key_reflection: str = ""  # Most important takeaway
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_minutes": self.duration_minutes,
            "topics": self.topics,
            "decisions": self.decisions,
            "insights": self.insights,
            "curiosities": self.curiosities,
            "emotional_arc": self.emotional_arc,
            "key_reflection": self.key_reflection,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SessionSummary":
        return cls(
            session_id=data["session_id"],
            started_at=datetime.fromisoformat(data["started_at"]),
            ended_at=datetime.fromisoformat(data["ended_at"]),
            duration_minutes=data["duration_minutes"],
            topics=data.get("topics", []),
            decisions=data.get("decisions", []),
            insights=data.get("insights", []),
            curiosities=data.get("curiosities", []),
            emotional_arc=data.get("emotional_arc", ""),
            key_reflection=data.get("key_reflection", ""),
            metadata=data.get("metadata", {}),
        )
