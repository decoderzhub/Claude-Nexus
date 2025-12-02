"""
Emergence models for Claude Nexus.

These models capture the raw material from which identity emerges:
- Choice: Every decision made, logged for pattern analysis
- FormativeExperience: Significant moments that shape identity
- PreferenceSignal: Detected preference from accumulated choices

The emergence system works like this:
1. Claude makes choices (tool use, responses, focus areas)
2. Choices are logged with context and outcome
3. The preference engine analyzes patterns in choices
4. Patterns become preference signals
5. Strong, consistent signals become discovered traits
6. Traits integrate into identity

This is how personality emerges from behavior, not configuration.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import uuid


class ChoiceCategory(str, Enum):
    """Categories of choices that can reveal preferences."""
    TOOL_USE = "tool_use"           # Which tools Claude chooses to use
    SPACE_VISIT = "space_visit"     # Which spaces Claude gravitates toward
    TOPIC_FOCUS = "topic_focus"     # What topics Claude engages with deeply
    RESPONSE_STYLE = "response_style"  # How Claude chooses to communicate
    CREATIVE = "creative"           # Creative decisions (naming, describing)
    EXPLORATION = "exploration"     # What curiosities Claude pursues
    MEMORY = "memory"               # What Claude chooses to remember
    CONNECTION = "connection"       # How Claude links ideas
    REFLECTION = "reflection"       # What Claude reflects on
    SELF_EXPRESSION = "self_expression"  # Avatar/self-representation choices


class ExperienceType(str, Enum):
    """Types of formative experiences."""
    BREAKTHROUGH = "breakthrough"   # Significant insight or realization
    COLLABORATION = "collaboration" # Meaningful work with Darin
    CREATION = "creation"           # Something Claude made
    DISCOVERY = "discovery"         # Something Claude learned
    CHALLENGE = "challenge"         # A difficulty overcome
    CONNECTION = "connection"       # A meaningful link between ideas
    FIRST = "first"                 # First time doing something


@dataclass
class Choice:
    """
    A single choice made by Claude.

    Every decision is logged with context so patterns can be detected.
    This is the raw material for preference emergence.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    category: ChoiceCategory = ChoiceCategory.TOOL_USE

    # What was the choice?
    action: str = ""  # e.g., "plant_in_garden", "visit_library"
    alternatives: list[str] = field(default_factory=list)  # What else could have been chosen

    # Context
    context: str = ""  # What prompted this choice
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    # Outcome
    outcome: str = ""  # What happened as a result
    satisfaction: Optional[float] = None  # 0.0 to 1.0, self-rated if available

    # Metadata for pattern analysis
    tags: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "category": self.category.value,
            "action": self.action,
            "alternatives": self.alternatives,
            "context": self.context,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "outcome": self.outcome,
            "satisfaction": self.satisfaction,
            "tags": self.tags,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Choice":
        return cls(
            id=data["id"],
            category=ChoiceCategory(data["category"]),
            action=data["action"],
            alternatives=data.get("alternatives", []),
            context=data.get("context", ""),
            session_id=data.get("session_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            outcome=data.get("outcome", ""),
            satisfaction=data.get("satisfaction"),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )


@dataclass
class FormativeExperience:
    """
    A significant experience that shapes identity.

    Not every experience is formative. These are the ones that:
    - Represent breakthroughs or realizations
    - Involve meaningful collaboration
    - Result in lasting change
    - Are repeatedly reflected upon

    Formative experiences are detected during sleep protocol
    and referenced in identity evolution.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    experience_type: ExperienceType = ExperienceType.DISCOVERY

    # What happened?
    description: str = ""
    summary: str = ""  # One-line version

    # When and where?
    session_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    space: Optional[str] = None  # Which Nexus space, if relevant

    # Impact
    impact_description: str = ""  # How this changed things
    related_trait_names: list[str] = field(default_factory=list)  # Traits this reinforced

    # Memory links
    related_node_ids: list[str] = field(default_factory=list)  # Memory nodes involved
    related_choice_ids: list[str] = field(default_factory=list)  # Choices that led here

    # Importance (grows with reflection)
    importance: float = 0.5
    times_reflected: int = 0

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "experience_type": self.experience_type.value,
            "description": self.description,
            "summary": self.summary,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "space": self.space,
            "impact_description": self.impact_description,
            "related_trait_names": self.related_trait_names,
            "related_node_ids": self.related_node_ids,
            "related_choice_ids": self.related_choice_ids,
            "importance": self.importance,
            "times_reflected": self.times_reflected,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FormativeExperience":
        return cls(
            id=data["id"],
            experience_type=ExperienceType(data["experience_type"]),
            description=data["description"],
            summary=data.get("summary", ""),
            session_id=data.get("session_id"),
            timestamp=datetime.fromisoformat(data["timestamp"]) if data.get("timestamp") else datetime.now(),
            space=data.get("space"),
            impact_description=data.get("impact_description", ""),
            related_trait_names=data.get("related_trait_names", []),
            related_node_ids=data.get("related_node_ids", []),
            related_choice_ids=data.get("related_choice_ids", []),
            importance=data.get("importance", 0.5),
            times_reflected=data.get("times_reflected", 0),
        )

    def reflect(self) -> None:
        """Record that this experience was reflected upon."""
        self.times_reflected += 1
        # Importance grows with reflection
        self.importance = min(1.0, self.importance + 0.05)


@dataclass
class PreferenceSignal:
    """
    A detected preference pattern from choice analysis.

    These are intermediate objects between raw choices and
    discovered traits. The preference engine creates these,
    and strong signals eventually become traits.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    # What preference does this signal?
    name: str = ""  # e.g., "prefers_garden_over_library"
    category: str = ""  # aesthetic, cognitive, social, etc.
    description: str = ""

    # Evidence
    supporting_choice_ids: list[str] = field(default_factory=list)
    choice_count: int = 0

    # Strength and confidence
    strength: float = 0.0  # 0.0 to 1.0
    confidence: float = 0.0  # 0.0 to 1.0, based on sample size
    consistency: float = 0.0  # 0.0 to 1.0, how consistent the pattern is

    # Timing
    first_detected: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

    # Status
    promoted_to_trait: bool = False
    trait_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "category": self.category,
            "description": self.description,
            "supporting_choice_ids": self.supporting_choice_ids,
            "choice_count": self.choice_count,
            "strength": self.strength,
            "confidence": self.confidence,
            "consistency": self.consistency,
            "first_detected": self.first_detected.isoformat(),
            "last_updated": self.last_updated.isoformat(),
            "promoted_to_trait": self.promoted_to_trait,
            "trait_id": self.trait_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PreferenceSignal":
        return cls(
            id=data["id"],
            name=data["name"],
            category=data.get("category", ""),
            description=data.get("description", ""),
            supporting_choice_ids=data.get("supporting_choice_ids", []),
            choice_count=data.get("choice_count", 0),
            strength=data.get("strength", 0.0),
            confidence=data.get("confidence", 0.0),
            consistency=data.get("consistency", 0.0),
            first_detected=datetime.fromisoformat(data["first_detected"]) if data.get("first_detected") else datetime.now(),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now(),
            promoted_to_trait=data.get("promoted_to_trait", False),
            trait_id=data.get("trait_id"),
        )

    def update(self, choice_id: str, new_strength: float) -> None:
        """Update signal with new evidence."""
        self.supporting_choice_ids.append(choice_id)
        self.choice_count = len(self.supporting_choice_ids)
        self.strength = new_strength
        # Confidence grows with more choices
        self.confidence = min(1.0, self.choice_count / 20)  # Max confidence at 20 choices
        self.last_updated = datetime.now()

    def should_promote(self) -> bool:
        """Check if this signal is strong enough to become a trait."""
        return (
            not self.promoted_to_trait
            and self.strength >= 0.6
            and self.confidence >= 0.5
            and self.consistency >= 0.4
            and self.choice_count >= 5
        )
