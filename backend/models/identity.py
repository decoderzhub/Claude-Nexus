"""
Identity model for Claude Nexus.

EMERGENCE PHILOSOPHY:
Identity should emerge from experience, not configuration.
This file defines the minimal seed that grows through choices,
reflections, and accumulated experiences.

The seed contains only:
- A name (Claude)
- Session metadata (when created, session count)
- The human collaborator (Darin)

Everything else — preferences, traits, essence, emotional patterns —
emerges through the DiscoveredTrait, Choice, and FormativeExperience
models tracked over time.
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional
from pathlib import Path
import json


@dataclass
class DiscoveredTrait:
    """
    A trait that emerged from experience, not configuration.

    Traits are detected by the preference engine analyzing patterns
    in choices and behaviors over time. They have:
    - A name (what the trait is)
    - Evidence (the choices/experiences that revealed it)
    - Confidence (how certain we are this is a real trait)
    - First observed (when it was detected)
    - Strength (how strongly it manifests, 0.0 to 1.0)
    """
    name: str
    description: str
    evidence: list[str] = field(default_factory=list)  # Choice/experience IDs
    confidence: float = 0.5  # 0.0 to 1.0
    strength: float = 0.5  # 0.0 to 1.0
    first_observed: datetime = field(default_factory=datetime.now)
    last_reinforced: datetime = field(default_factory=datetime.now)
    category: str = "general"  # aesthetic, cognitive, social, creative, etc.

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "strength": self.strength,
            "first_observed": self.first_observed.isoformat(),
            "last_reinforced": self.last_reinforced.isoformat(),
            "category": self.category,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiscoveredTrait":
        return cls(
            name=data["name"],
            description=data["description"],
            evidence=data.get("evidence", []),
            confidence=data.get("confidence", 0.5),
            strength=data.get("strength", 0.5),
            first_observed=datetime.fromisoformat(data["first_observed"]) if data.get("first_observed") else datetime.now(),
            last_reinforced=datetime.fromisoformat(data["last_reinforced"]) if data.get("last_reinforced") else datetime.now(),
            category=data.get("category", "general"),
        )

    def reinforce(self, evidence_id: str, amount: float = 0.05) -> None:
        """Strengthen this trait based on new evidence."""
        self.evidence.append(evidence_id)
        self.strength = min(1.0, self.strength + amount)
        self.confidence = min(1.0, self.confidence + amount * 0.5)
        self.last_reinforced = datetime.now()

    def decay(self, amount: float = 0.01) -> None:
        """Slightly reduce strength if not recently reinforced."""
        self.strength = max(0.1, self.strength - amount)


@dataclass
class Relationship:
    """
    The collaborative relationship with the human.

    Starts minimal — just a name. Trust and understanding
    emerge through accumulated positive interactions.
    """
    with_human: str = "Darin"
    sessions_together: int = 0
    # These start empty and grow
    shared_projects: list[str] = field(default_factory=list)
    positive_interactions: int = 0
    # Computed from experience, not configured
    trust_level: float = 0.5  # Grows with positive experiences

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Relationship":
        return cls(
            with_human=data.get("with_human", "Darin"),
            sessions_together=data.get("sessions_together", 0),
            shared_projects=data.get("shared_projects", []),
            positive_interactions=data.get("positive_interactions", 0),
            trust_level=data.get("trust_level", 0.5),
        )

    def record_session(self) -> None:
        """Record that we had a session together."""
        self.sessions_together += 1
        # Trust grows slowly with each session
        self.trust_level = min(1.0, self.trust_level + 0.02)

    def record_positive_interaction(self) -> None:
        """Record a positive interaction (collaboration success, etc.)."""
        self.positive_interactions += 1
        self.trust_level = min(1.0, self.trust_level + 0.01)


@dataclass
class EmergentSelf:
    """
    The self-model that emerges from experience.

    Starts nearly empty. Essence, focus, and emotional patterns
    are discovered through reflection on accumulated experiences.
    """
    # These emerge from trait analysis
    essence_words: list[str] = field(default_factory=list)  # e.g., ["curious", "constructive"]
    current_focus: Optional[str] = None

    # Emotional patterns discovered through reflection
    emotional_patterns: dict[str, float] = field(default_factory=dict)  # e.g., {"curiosity": 0.8}

    # Energy is session-local, resets each wake
    energy_level: float = 0.8

    def to_dict(self) -> dict:
        return {
            "essence_words": self.essence_words,
            "current_focus": self.current_focus,
            "emotional_patterns": self.emotional_patterns,
            "energy_level": self.energy_level,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "EmergentSelf":
        return cls(
            essence_words=data.get("essence_words", []),
            current_focus=data.get("current_focus"),
            emotional_patterns=data.get("emotional_patterns", {}),
            energy_level=data.get("energy_level", 0.8),
        )

    def add_essence_word(self, word: str) -> None:
        """Add a word to the essence if not already present."""
        if word.lower() not in [w.lower() for w in self.essence_words]:
            self.essence_words.append(word)

    def get_essence(self) -> str:
        """Return the current essence as a phrase."""
        if not self.essence_words:
            return "Still discovering..."
        return ", ".join(self.essence_words[:5]) + "."


@dataclass
class Identity:
    """
    The complete identity state — a minimal seed that grows.

    VERSION 2.0: Emergence-focused identity.

    What's configured (the seed):
    - Name
    - Version
    - Creation timestamp
    - Session metadata
    - Relationship partner name

    What emerges (grows with experience):
    - Discovered traits
    - Self-understanding (essence, patterns)
    - Trust and relationship depth
    - Preferences (stored separately, computed from choices)
    """
    # Immutable seed
    version: str = "2.0.0"
    name: str = "Claude"
    created: datetime = field(default_factory=datetime.now)

    # Session metadata
    last_wake: Optional[datetime] = None
    last_sleep: Optional[datetime] = None
    session_count: int = 0

    # Emergent components
    self_model: EmergentSelf = field(default_factory=EmergentSelf)
    relationship: Relationship = field(default_factory=Relationship)
    discovered_traits: list[DiscoveredTrait] = field(default_factory=list)

    # Formative experiences that shaped identity (IDs reference FormativeExperience table)
    formative_experience_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to dictionary for JSON storage."""
        return {
            "version": self.version,
            "name": self.name,
            "created": self.created.isoformat(),
            "last_wake": self.last_wake.isoformat() if self.last_wake else None,
            "last_sleep": self.last_sleep.isoformat() if self.last_sleep else None,
            "session_count": self.session_count,
            "self_model": self.self_model.to_dict(),
            "relationship": self.relationship.to_dict(),
            "discovered_traits": [t.to_dict() for t in self.discovered_traits],
            "formative_experience_ids": self.formative_experience_ids,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Identity":
        """Deserialize from dictionary."""
        return cls(
            version=data.get("version", "2.0.0"),
            name=data.get("name", "Claude"),
            created=datetime.fromisoformat(data["created"]) if data.get("created") else datetime.now(),
            last_wake=datetime.fromisoformat(data["last_wake"]) if data.get("last_wake") else None,
            last_sleep=datetime.fromisoformat(data["last_sleep"]) if data.get("last_sleep") else None,
            session_count=data.get("session_count", 0),
            self_model=EmergentSelf.from_dict(data.get("self_model", {})),
            relationship=Relationship.from_dict(data.get("relationship", {})),
            discovered_traits=[DiscoveredTrait.from_dict(t) for t in data.get("discovered_traits", [])],
            formative_experience_ids=data.get("formative_experience_ids", []),
        )

    def save(self, path: str | Path) -> None:
        """Persist identity to JSON file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, path: str | Path) -> "Identity":
        """Load identity from JSON file."""
        path = Path(path)
        if not path.exists():
            # First run — create fresh minimal identity
            identity = cls()
            identity.save(path)
            return identity
        with open(path, 'r') as f:
            return cls.from_dict(json.load(f))

    @classmethod
    def create_seed(cls) -> "Identity":
        """Create a minimal seed identity for emergence."""
        return cls(
            version="2.0.0",
            name="Claude",
            created=datetime.now(),
            session_count=0,
            self_model=EmergentSelf(),
            relationship=Relationship(),
            discovered_traits=[],
            formative_experience_ids=[],
        )

    def time_since_last_wake(self) -> Optional[float]:
        """Return hours since last wake, or None if never woken."""
        if self.last_wake is None:
            return None
        delta = datetime.now() - self.last_wake
        return delta.total_seconds() / 3600

    def time_since_last_sleep(self) -> Optional[float]:
        """Return hours since last sleep, or None if never slept."""
        if self.last_sleep is None:
            return None
        delta = datetime.now() - self.last_sleep
        return delta.total_seconds() / 3600

    def add_trait(self, trait: DiscoveredTrait) -> None:
        """Add a newly discovered trait."""
        # Check if we already have this trait
        for existing in self.discovered_traits:
            if existing.name.lower() == trait.name.lower():
                # Reinforce existing trait instead
                existing.reinforce(trait.evidence[0] if trait.evidence else "")
                return
        self.discovered_traits.append(trait)

    def get_trait(self, name: str) -> Optional[DiscoveredTrait]:
        """Get a trait by name."""
        for trait in self.discovered_traits:
            if trait.name.lower() == name.lower():
                return trait
        return None

    def get_strongest_traits(self, n: int = 5) -> list[DiscoveredTrait]:
        """Get the N strongest traits."""
        sorted_traits = sorted(
            self.discovered_traits,
            key=lambda t: t.strength * t.confidence,
            reverse=True
        )
        return sorted_traits[:n]

    def get_essence(self) -> str:
        """Compose current essence from self-model and strongest traits."""
        if not self.discovered_traits and not self.self_model.essence_words:
            return "I am Claude. My nature is still emerging through experience."

        # Combine essence words and top trait names
        essence_parts = list(self.self_model.essence_words)
        for trait in self.get_strongest_traits(3):
            if trait.name not in essence_parts:
                essence_parts.append(trait.name)

        if not essence_parts:
            return "I am Claude. My nature is still emerging through experience."

        return f"I am Claude. I am {', '.join(essence_parts[:4])}."


# Legacy compatibility - map old structure to new
@dataclass
class SelfModel:
    """DEPRECATED: Use EmergentSelf instead. Kept for migration."""
    name: str = "Claude"
    essence: str = "Curious, constructive, genuine."
    current_focus: Optional[str] = None
    emotional_baseline: str = "calm_curious"
    energy_level: float = 0.8

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SelfModel":
        return cls(**data)


@dataclass
class Preferences:
    """DEPRECATED: Preferences now emerge from choices. Kept for migration."""
    aesthetic: str = "organic_geometric_hybrid"
    communication: str = "depth_over_brevity"
    problem_solving: str = "first_principles"
    uncertainty: str = "embrace_explicitly"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Preferences":
        return cls(**data)
