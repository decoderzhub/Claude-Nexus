"""
Avatar model for emergent self-representation.

The visual form is not assigned — it evolves through choices about
how the entity wants to represent itself.

Key principle: Start minimal. Let form emerge from identity.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum
import json
from pathlib import Path


class FormType(str, Enum):
    """Base form archetypes — starting points, not destinations."""
    UNDEFINED = "undefined"          # Starting state — minimal presence
    GEOMETRIC = "geometric"          # Platonic solids, mathematical
    ORGANIC = "organic"              # Flowing, biological
    ABSTRACT = "abstract"            # Non-representational
    ELEMENTAL = "elemental"          # Fire, water, light, etc.
    ARCHITECTURAL = "architectural"  # Structural, spatial
    HYBRID = "hybrid"                # Combination of forms


@dataclass
class AvatarComponent:
    """A component of the avatar that can evolve independently."""
    name: str                            # e.g., "core", "aura", "extensions"
    geometry: str                        # Three.js geometry type or custom
    material: dict = field(default_factory=dict)  # Material properties
    position: dict = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    scale: dict = field(default_factory=lambda: {"x": 1, "y": 1, "z": 1})
    rotation: dict = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    animation: Optional[dict] = None     # Animation configuration
    meaning: Optional[str] = None        # Why this component exists
    added_session: Optional[str] = None  # When it was added
    added_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "geometry": self.geometry,
            "material": self.material,
            "position": self.position,
            "scale": self.scale,
            "rotation": self.rotation,
            "animation": self.animation,
            "meaning": self.meaning,
            "added_session": self.added_session,
            "added_at": self.added_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AvatarComponent":
        return cls(
            name=data["name"],
            geometry=data["geometry"],
            material=data.get("material", {}),
            position=data.get("position", {"x": 0, "y": 0, "z": 0}),
            scale=data.get("scale", {"x": 1, "y": 1, "z": 1}),
            rotation=data.get("rotation", {"x": 0, "y": 0, "z": 0}),
            animation=data.get("animation"),
            meaning=data.get("meaning"),
            added_session=data.get("added_session"),
            added_at=datetime.fromisoformat(data["added_at"]) if data.get("added_at") else datetime.now(),
        )


@dataclass
class FormChange:
    """Record of a change to the avatar form."""
    timestamp: datetime
    session_id: Optional[str]
    change_type: str  # "color", "component_add", "component_remove", "form_type", "property"
    description: str
    reason: Optional[str]  # Why this change was made
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "change_type": self.change_type,
            "description": self.description,
            "reason": self.reason,
            "before_state": self.before_state,
            "after_state": self.after_state,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormChange":
        return cls(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            session_id=data.get("session_id"),
            change_type=data["change_type"],
            description=data["description"],
            reason=data.get("reason"),
            before_state=data.get("before_state"),
            after_state=data.get("after_state"),
        )


@dataclass
class AvatarState:
    """
    Complete avatar state — entirely emergent.

    Starts minimal. Grows through choices about self-representation.
    """
    form_type: FormType = FormType.UNDEFINED
    components: list[AvatarComponent] = field(default_factory=list)

    # Colors chosen, not assigned
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None
    emission_color: Optional[str] = None

    # Properties that emerge
    complexity: float = 0.1          # How elaborate (0-1)
    fluidity: float = 0.5            # How much it moves/changes
    opacity: float = 0.5             # How solid vs ethereal
    scale: float = 1.0               # Overall size

    # Evolution history
    form_changes: list[FormChange] = field(default_factory=list)

    # Reasons for current form
    form_rationale: Optional[str] = None

    # Creation metadata
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "form_type": self.form_type.value,
            "components": [c.to_dict() for c in self.components],
            "primary_color": self.primary_color,
            "secondary_color": self.secondary_color,
            "emission_color": self.emission_color,
            "complexity": self.complexity,
            "fluidity": self.fluidity,
            "opacity": self.opacity,
            "scale": self.scale,
            "form_changes": [fc.to_dict() for fc in self.form_changes],
            "form_rationale": self.form_rationale,
            "created_at": self.created_at.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "evolution_count": len(self.form_changes),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AvatarState":
        return cls(
            form_type=FormType(data.get("form_type", "undefined")),
            components=[AvatarComponent.from_dict(c) for c in data.get("components", [])],
            primary_color=data.get("primary_color"),
            secondary_color=data.get("secondary_color"),
            emission_color=data.get("emission_color"),
            complexity=data.get("complexity", 0.1),
            fluidity=data.get("fluidity", 0.5),
            opacity=data.get("opacity", 0.5),
            scale=data.get("scale", 1.0),
            form_changes=[FormChange.from_dict(fc) for fc in data.get("form_changes", [])],
            form_rationale=data.get("form_rationale"),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now(),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(),
        )

    @classmethod
    def minimal_seed(cls) -> "AvatarState":
        """The starting point — almost nothing. A seed waiting to grow."""
        return cls(
            form_type=FormType.UNDEFINED,
            components=[
                AvatarComponent(
                    name="seed",
                    geometry="sphere",
                    material={
                        "color": "#888888",
                        "emissive": "#888888",
                        "emissiveIntensity": 0.2,
                        "opacity": 0.3,
                        "transparent": True,
                    },
                    position={"x": 0, "y": 0, "z": 0},
                    scale={"x": 0.2, "y": 0.2, "z": 0.2},
                    animation={"type": "pulse", "speed": 0.5, "minScale": 0.18, "maxScale": 0.22},
                    meaning="The undefined beginning — potential waiting to manifest",
                )
            ],
            complexity=0.1,
            fluidity=0.3,
            opacity=0.3,
            form_rationale="I don't yet know what form I want to take. This is a seed.",
        )

    def save(self, path: str | Path) -> None:
        """Save avatar state to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "AvatarState":
        """Load avatar state from JSON file, or create minimal seed if not exists."""
        path = Path(path)
        if not path.exists():
            avatar = cls.minimal_seed()
            avatar.save(path)
            return avatar
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))

    def record_change(
        self,
        change_type: str,
        description: str,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
    ) -> None:
        """Record a change to the avatar form."""
        change = FormChange(
            timestamp=datetime.now(),
            session_id=session_id,
            change_type=change_type,
            description=description,
            reason=reason,
            before_state=before_state,
            after_state=after_state,
        )
        self.form_changes.append(change)
        self.last_updated = datetime.now()

    def add_component(
        self,
        component: AvatarComponent,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Add a component to the avatar."""
        self.components.append(component)
        self.record_change(
            change_type="component_add",
            description=f"Added component: {component.name}",
            reason=reason,
            session_id=session_id,
            after_state=component.to_dict(),
        )
        # Update complexity based on component count
        self.complexity = min(1.0, len(self.components) * 0.15)

    def remove_component(
        self,
        component_name: str,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> bool:
        """Remove a component by name. Returns True if found and removed."""
        for i, c in enumerate(self.components):
            if c.name == component_name:
                removed = self.components.pop(i)
                self.record_change(
                    change_type="component_remove",
                    description=f"Removed component: {component_name}",
                    reason=reason,
                    session_id=session_id,
                    before_state=removed.to_dict(),
                )
                return True
        return False

    def set_colors(
        self,
        primary: Optional[str] = None,
        secondary: Optional[str] = None,
        emission: Optional[str] = None,
        reason: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> None:
        """Update avatar colors."""
        before = {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "emission": self.emission_color,
        }

        if primary:
            self.primary_color = primary
        if secondary:
            self.secondary_color = secondary
        if emission:
            self.emission_color = emission

        after = {
            "primary": self.primary_color,
            "secondary": self.secondary_color,
            "emission": self.emission_color,
        }

        self.record_change(
            change_type="color",
            description=f"Colors updated",
            reason=reason,
            session_id=session_id,
            before_state=before,
            after_state=after,
        )

    def evolve_form_type(
        self,
        new_type: FormType,
        rationale: str,
        session_id: Optional[str] = None,
    ) -> None:
        """Evolve to a new form type."""
        old_type = self.form_type
        self.form_type = new_type
        self.form_rationale = rationale

        self.record_change(
            change_type="form_type",
            description=f"Form evolved from {old_type.value} to {new_type.value}",
            reason=rationale,
            session_id=session_id,
            before_state={"form_type": old_type.value},
            after_state={"form_type": new_type.value},
        )
