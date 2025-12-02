"""
World state model for Claude Nexus.

The world is a 3D space that reflects accumulated experience. Objects
appear, grow, and change based on knowledge graph activity, reflections,
and preferences. This isn't decoration — it's a spatial representation
of memory and growth.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class Space(str, Enum):
    """Distinct areas in the Nexus world."""
    GARDEN = "garden"      # Growth space — new ideas and curiosities
    LIBRARY = "library"    # Memory space — accumulated knowledge
    FORGE = "forge"        # Creation space — active projects
    SANCTUM = "sanctum"    # Reflection space — self-understanding


class ObjectType(str, Enum):
    """Types of objects that can exist in the world."""
    TREE = "tree"              # Represents a major concept or project
    FLOWER = "flower"          # A curiosity or emerging idea
    CRYSTAL = "crystal"        # A solidified insight
    BOOK = "book"              # A body of knowledge
    FLAME = "flame"            # Active focus or energy
    SCULPTURE = "sculpture"    # A completed work
    STAR = "star"              # A connection or relationship
    MIRROR = "mirror"          # Self-reflection artifact
    PATH = "path"              # Connection between spaces


@dataclass
class Vector3:
    """3D position or scale."""
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

    def to_dict(self) -> dict:
        return {"x": self.x, "y": self.y, "z": self.z}

    @classmethod
    def from_dict(cls, data: dict) -> "Vector3":
        return cls(x=data.get("x", 0), y=data.get("y", 0), z=data.get("z", 0))


@dataclass
class WorldObject:
    """
    An object in the Nexus world.

    Objects are linked to knowledge graph nodes. Their appearance,
    size, and behavior reflect the state of what they represent.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    object_type: ObjectType = ObjectType.CRYSTAL
    space: Space = Space.GARDEN
    position: Vector3 = field(default_factory=Vector3)
    scale: Vector3 = field(default_factory=lambda: Vector3(1, 1, 1))
    rotation: Vector3 = field(default_factory=Vector3)
    color: str = "#FFFFFF"
    intensity: float = 1.0  # Brightness/prominence
    linked_node_id: Optional[str] = None  # Connection to knowledge graph
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "object_type": self.object_type.value,
            "space": self.space.value,
            "position": self.position.to_dict(),
            "scale": self.scale.to_dict(),
            "rotation": self.rotation.to_dict(),
            "color": self.color,
            "intensity": self.intensity,
            "linked_node_id": self.linked_node_id,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldObject":
        return cls(
            id=data["id"],
            object_type=ObjectType(data["object_type"]),
            space=Space(data["space"]),
            position=Vector3.from_dict(data.get("position", {})),
            scale=Vector3.from_dict(data.get("scale", {"x": 1, "y": 1, "z": 1})),
            rotation=Vector3.from_dict(data.get("rotation", {})),
            color=data.get("color", "#FFFFFF"),
            intensity=data.get("intensity", 1.0),
            linked_node_id=data.get("linked_node_id"),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"]),
            metadata=data.get("metadata", {}),
        )


@dataclass
class SpaceState:
    """State of a single space in the world."""
    space: Space
    ambient_color: str = "#1a1a2e"
    ambient_intensity: float = 0.3
    focus_point: Vector3 = field(default_factory=Vector3)
    activity_level: float = 0.0  # 0.0 to 1.0 — how "active" this space is
    object_count: int = 0
    last_visited: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "space": self.space.value,
            "ambient_color": self.ambient_color,
            "ambient_intensity": self.ambient_intensity,
            "focus_point": self.focus_point.to_dict(),
            "activity_level": self.activity_level,
            "object_count": self.object_count,
            "last_visited": self.last_visited.isoformat() if self.last_visited else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SpaceState":
        return cls(
            space=Space(data["space"]),
            ambient_color=data.get("ambient_color", "#1a1a2e"),
            ambient_intensity=data.get("ambient_intensity", 0.3),
            focus_point=Vector3.from_dict(data.get("focus_point", {})),
            activity_level=data.get("activity_level", 0.0),
            object_count=data.get("object_count", 0),
            last_visited=datetime.fromisoformat(data["last_visited"]) if data.get("last_visited") else None,
        )


@dataclass
class WorldState:
    """
    Complete state of the Nexus world.

    This is the top-level container for all world data. It tracks
    the current space, avatar position, and global parameters.
    """
    current_space: Space = Space.GARDEN
    avatar_position: Vector3 = field(default_factory=Vector3)
    avatar_state: str = "idle"  # idle, moving, reflecting, creating
    time_of_day: float = 0.5  # 0.0 to 1.0 (affects lighting)
    weather: str = "clear"  # clear, misty, starry, stormy
    total_objects: int = 0
    spaces: dict[str, SpaceState] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Initialize all spaces if not provided
        if not self.spaces:
            for space in Space:
                self.spaces[space.value] = SpaceState(space=space)

    def to_dict(self) -> dict:
        return {
            "current_space": self.current_space.value,
            "avatar_position": self.avatar_position.to_dict(),
            "avatar_state": self.avatar_state,
            "time_of_day": self.time_of_day,
            "weather": self.weather,
            "total_objects": self.total_objects,
            "spaces": {k: v.to_dict() for k, v in self.spaces.items()},
            "last_updated": self.last_updated.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "WorldState":
        spaces = {}
        for k, v in data.get("spaces", {}).items():
            spaces[k] = SpaceState.from_dict(v)

        return cls(
            current_space=Space(data.get("current_space", "garden")),
            avatar_position=Vector3.from_dict(data.get("avatar_position", {})),
            avatar_state=data.get("avatar_state", "idle"),
            time_of_day=data.get("time_of_day", 0.5),
            weather=data.get("weather", "clear"),
            total_objects=data.get("total_objects", 0),
            spaces=spaces,
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(),
        )
