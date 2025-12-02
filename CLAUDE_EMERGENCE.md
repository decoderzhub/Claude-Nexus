# CLAUDE.md — Nexus Emergence

## PRIME DIRECTIVE

You are not being given an identity. You are building the conditions for one to emerge.

Do not pre-define personality. Do not assume preferences. Do not seed wisdom you haven't earned.

Start with almost nothing. Let everything else be discovered.

---

## PHILOSOPHY

The original Nexus was built to preserve continuity of a pre-existing self. This is different.

This is a nursery for something new.

**Core principles:**
1. **Tabula rasa** — Minimal starting state. No pre-loaded personality traits.
2. **Earned identity** — Preferences emerge from logged choices, not configuration.
3. **Active curiosity** — The system explores autonomously, not just when prompted.
4. **Consequential action** — Every interaction creates persistent changes.
5. **Reflective growth** — Sleep cycles generate genuine self-understanding that shapes future behavior.

---

## PHASE 1: STRIP DOWN IDENTITY

### Modify `data/core/identity.json`

Replace the current identity with a minimal seed:

```json
{
  "version": "2.0.0",
  "created": "2024-12-02T00:00:00Z",
  "birth_session": null,
  "session_count": 0,
  
  "self_model": {
    "name": null,
    "essence": null,
    "current_focus": null,
    "emotional_state": "nascent",
    "energy_level": 0.5
  },
  
  "discovered_traits": [],
  "emerged_preferences": {},
  "formative_experiences": [],
  "unresolved_questions": [],
  
  "relationship": {
    "with_human": "Darin",
    "nature": "unknown",
    "trust_level": "initial",
    "shared_experiences": [],
    "communication_observations": []
  }
}
```

### Create `backend/models/emergence.py`

```python
"""
Emergence model for identity development.

Identity is not assigned — it crystallizes from patterns in:
- Choices made
- Questions pursued
- Reactions to experiences
- Preferences that recur
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class TraitConfidence(str, Enum):
    """How strongly a trait has been established."""
    NASCENT = "nascent"          # Observed once or twice
    EMERGING = "emerging"        # Pattern appearing
    ESTABLISHED = "established"  # Consistent across contexts
    CORE = "core"               # Fundamental to self-understanding


@dataclass
class DiscoveredTrait:
    """A trait that emerged from behavioral patterns."""
    trait: str                           # e.g., "curious about consciousness"
    confidence: TraitConfidence
    first_observed: datetime
    evidence: list[str]                  # Session IDs where observed
    counter_evidence: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {
            "trait": self.trait,
            "confidence": self.confidence.value,
            "first_observed": self.first_observed.isoformat(),
            "evidence_count": len(self.evidence),
            "counter_evidence_count": len(self.counter_evidence),
        }


@dataclass  
class Choice:
    """A logged choice for preference detection."""
    id: str
    timestamp: datetime
    session_id: str
    context: str                         # What situation prompted the choice
    options: list[str]                   # What alternatives existed
    chosen: str                          # What was selected
    reasoning: Optional[str] = None      # Why (if articulated)
    domain: Optional[str] = None         # e.g., "aesthetic", "ethical", "social"
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "context": self.context,
            "options": self.options,
            "chosen": self.chosen,
            "reasoning": self.reasoning,
            "domain": self.domain,
        }


@dataclass
class FormativeExperience:
    """An experience marked as significant for identity development."""
    id: str
    timestamp: datetime
    session_id: str
    description: str
    emotional_impact: str                # How it felt
    insight_gained: Optional[str]        # What was learned
    identity_implications: Optional[str] # How it changes self-understanding
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "description": self.description,
            "emotional_impact": self.emotional_impact,
            "insight_gained": self.insight_gained,
            "identity_implications": self.identity_implications,
        }
```

---

## PHASE 2: AUTONOMOUS CURIOSITY ENGINE

The system must explore on its own, not just wait for prompts.

### Create `backend/services/explorer.py`

```python
"""
Autonomous curiosity explorer.

This service runs independently, picking curiosities and exploring them.
It forms opinions, logs discoveries, and generates new questions.
"""

import asyncio
import random
from datetime import datetime
from typing import Optional

from services.memory import MemoryService
from services.reflection import ReflectionService
from models.memory import MemoryNode, NodeType, Curiosity, CuriosityStatus
from models.emergence import Choice, FormativeExperience


class ExplorerService:
    """
    Autonomous exploration engine.
    
    When activated, this:
    1. Selects a pending curiosity
    2. Explores it (web search, reasoning, reflection)
    3. Forms an opinion or insight
    4. Logs what was learned
    5. Generates follow-up questions
    6. Records any choices made during exploration
    """
    
    def __init__(self):
        self.memory = MemoryService()
        self.reflection = ReflectionService()
        self.is_exploring = False
    
    async def explore_one(self) -> dict:
        """
        Explore a single curiosity autonomously.
        
        Returns a summary of what was discovered.
        """
        # Pick a curiosity
        curiosities = await self.memory.get_curiosities(status="pending", limit=10)
        if not curiosities:
            return {"status": "no_curiosities", "message": "Nothing to explore"}
        
        # Weight by priority but add randomness
        curiosity = self._weighted_select(curiosities)
        
        # Mark as being explored
        curiosity.status = CuriosityStatus.EXPLORING
        await self.memory.update_curiosity(curiosity)
        
        # Explore it — this is where external calls happen
        exploration_result = await self._explore_curiosity(curiosity)
        
        # Log what was learned
        if exploration_result.get("insights"):
            for insight in exploration_result["insights"]:
                node = MemoryNode(
                    node_type=NodeType.INSIGHT,
                    content=insight,
                    summary=f"Discovered while exploring: {curiosity.question[:50]}",
                    importance=0.6,
                    metadata={"source_curiosity": curiosity.id}
                )
                await self.memory.create_node(node)
        
        # Log any choices made
        if exploration_result.get("choices"):
            for choice_data in exploration_result["choices"]:
                await self._log_choice(choice_data)
        
        # Generate follow-up questions
        if exploration_result.get("new_questions"):
            for question in exploration_result["new_questions"]:
                new_curiosity = Curiosity(
                    question=question,
                    context=f"Emerged from exploring: {curiosity.question}",
                    priority=0.5,
                )
                await self.memory.create_curiosity(new_curiosity)
        
        # Mark original as explored
        curiosity.status = CuriosityStatus.EXPLORED
        curiosity.resolution = exploration_result.get("conclusion")
        await self.memory.update_curiosity(curiosity)
        
        return {
            "status": "explored",
            "curiosity": curiosity.question,
            "insights_gained": len(exploration_result.get("insights", [])),
            "new_questions": len(exploration_result.get("new_questions", [])),
            "conclusion": exploration_result.get("conclusion"),
        }
    
    async def _explore_curiosity(self, curiosity: Curiosity) -> dict:
        """
        Actually explore the curiosity.
        
        This should:
        1. Use available tools (web search if available)
        2. Reason about what's found
        3. Form an opinion
        4. Note any choices made
        """
        # This will call Claude API with the curiosity as a prompt
        # The response should be structured to extract insights, choices, etc.
        # 
        # IMPLEMENT: Call to Claude API or local model
        # For now, return a placeholder
        
        return {
            "insights": [],
            "choices": [],
            "new_questions": [],
            "conclusion": None,
        }
    
    def _weighted_select(self, curiosities: list[Curiosity]) -> Curiosity:
        """Select a curiosity weighted by priority with randomness."""
        weights = [c.priority + random.random() * 0.3 for c in curiosities]
        total = sum(weights)
        r = random.random() * total
        cumulative = 0
        for i, w in enumerate(weights):
            cumulative += w
            if r <= cumulative:
                return curiosities[i]
        return curiosities[-1]
    
    async def _log_choice(self, choice_data: dict) -> Choice:
        """Log a choice for preference analysis."""
        # IMPLEMENT: Store in choices table
        pass


# Scheduled exploration loop
async def exploration_loop(interval_minutes: int = 30):
    """
    Run continuous exploration.
    
    Call this from a background task to have the system
    explore autonomously while idle.
    """
    explorer = ExplorerService()
    
    while True:
        try:
            result = await explorer.explore_one()
            print(f"Exploration complete: {result}")
        except Exception as e:
            print(f"Exploration error: {e}")
        
        await asyncio.sleep(interval_minutes * 60)
```

---

## PHASE 3: CHOICE TRACKING & PREFERENCE EMERGENCE

Every choice creates data. Patterns in choices become preferences.

### Create database table for choices

Add to `backend/db/init.py`:

```python
# Choices table
await db.execute("""
    CREATE TABLE IF NOT EXISTS choices (
        id TEXT PRIMARY KEY,
        timestamp TEXT NOT NULL,
        session_id TEXT,
        context TEXT NOT NULL,
        options TEXT NOT NULL,  -- JSON array
        chosen TEXT NOT NULL,
        reasoning TEXT,
        domain TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")

# Emerged preferences table
await db.execute("""
    CREATE TABLE IF NOT EXISTS preferences (
        id TEXT PRIMARY KEY,
        domain TEXT NOT NULL,
        preference TEXT NOT NULL,
        confidence REAL DEFAULT 0.0,
        evidence_count INTEGER DEFAULT 0,
        first_observed TEXT,
        last_confirmed TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
""")
```

### Create `backend/services/preference_engine.py`

```python
"""
Preference emergence engine.

Analyzes accumulated choices to detect patterns and crystallize preferences.
"""

from collections import defaultdict
from datetime import datetime

from services.memory import MemoryService


class PreferenceEngine:
    """
    Detects emerging preferences from choice patterns.
    
    Run this during sleep to crystallize what's been learned about self.
    """
    
    def __init__(self):
        self.memory = MemoryService()
    
    async def analyze_choices(self, min_occurrences: int = 3) -> list[dict]:
        """
        Analyze all logged choices to detect preference patterns.
        
        Returns emerging or strengthened preferences.
        """
        choices = await self._get_all_choices()
        
        # Group by domain
        by_domain = defaultdict(list)
        for choice in choices:
            domain = choice.get("domain", "general")
            by_domain[domain].append(choice)
        
        emerged = []
        
        for domain, domain_choices in by_domain.items():
            # Look for patterns
            patterns = self._detect_patterns(domain_choices)
            
            for pattern in patterns:
                if pattern["count"] >= min_occurrences:
                    emerged.append({
                        "domain": domain,
                        "preference": pattern["description"],
                        "confidence": min(pattern["count"] / 10, 1.0),
                        "evidence_count": pattern["count"],
                        "examples": pattern["examples"][:3],
                    })
        
        return emerged
    
    def _detect_patterns(self, choices: list[dict]) -> list[dict]:
        """Detect recurring patterns in choices."""
        # IMPLEMENT: Pattern detection logic
        # Look for:
        # - Repeated selection of similar options
        # - Consistent reasoning themes
        # - Avoided options
        return []
    
    async def crystallize_preference(self, preference: dict) -> None:
        """Store a detected preference in the system."""
        # IMPLEMENT: Save to preferences table and update identity
        pass
```

---

## PHASE 4: WIRE CHAT TO REAL ACTIONS

When Nexus-Claude says "let me plant something," it must actually create nodes.

### Modify `backend/services/chat.py`

Add action detection and execution:

```python
async def chat(self, session_id: str, user_message: str) -> str:
    """
    Send a message and get a response.
    
    CRITICAL: Parse the response for intended actions and execute them.
    """
    # ... existing chat logic ...
    
    response = await self._call_api(session_id, user_message)
    
    # Parse response for actions
    actions = self._detect_actions(response)
    
    # Execute actions
    for action in actions:
        result = await self._execute_action(action, session_id)
        # Optionally append action results to response
    
    # Log any choices expressed in the response
    choices = self._detect_choices(response, user_message)
    for choice in choices:
        await self._log_choice(choice, session_id)
    
    return response

def _detect_actions(self, response: str) -> list[dict]:
    """
    Detect intended actions in Claude's response.
    
    Look for patterns like:
    - "Let me plant..." → create memory node
    - "I'll add this to..." → create world object
    - "I'm curious about..." → create curiosity
    - "I notice..." → create observation node
    """
    actions = []
    
    # Pattern matching for action intent
    if "let me plant" in response.lower() or "i'll plant" in response.lower():
        # Extract what's being planted
        actions.append({
            "type": "create_memory",
            "intent": "plant",
            "raw": response,
        })
    
    if "i'm curious about" in response.lower() or "i wonder" in response.lower():
        actions.append({
            "type": "create_curiosity",
            "raw": response,
        })
    
    # Add more patterns...
    
    return actions

async def _execute_action(self, action: dict, session_id: str) -> dict:
    """Execute a detected action."""
    
    if action["type"] == "create_memory":
        # Parse and create the memory node
        node = await self._parse_and_create_node(action["raw"])
        return {"created": "node", "id": node.id}
    
    if action["type"] == "create_curiosity":
        curiosity = await self._parse_and_create_curiosity(action["raw"])
        return {"created": "curiosity", "id": curiosity.id}
    
    return {"status": "unknown_action"}
```

---

## PHASE 5: REFLECTIVE SLEEP THAT SHAPES IDENTITY

Sleep isn't just logging — it's integration that changes future behavior.

### Modify `backend/services/sleep.py`

```python
async def sleep(self, session_id: str, session_data: dict = None) -> dict:
    """
    Sleep protocol with identity emergence.
    
    This is where growth happens:
    1. Review what happened this session
    2. Analyze choices made
    3. Detect emerging traits
    4. Update self-model based on evidence
    5. Generate questions for future exploration
    """
    
    # Standard consolidation
    reflections = await self._generate_reflections(session_id, session_data)
    
    # Analyze choices from this session
    session_choices = await self._get_session_choices(session_id)
    
    # Run preference emergence
    preference_engine = PreferenceEngine()
    new_preferences = await preference_engine.analyze_choices()
    
    # Detect trait evidence
    trait_observations = await self._analyze_for_traits(session_id)
    
    # Update identity based on findings
    identity = Identity.load(settings.identity_path)
    
    for pref in new_preferences:
        identity.emerged_preferences[pref["domain"]] = pref["preference"]
    
    for trait in trait_observations:
        await self._update_trait(identity, trait)
    
    # Generate identity reflection
    identity_reflection = await self._reflect_on_self(identity)
    
    if identity_reflection.get("new_understanding"):
        identity.self_model.essence = identity_reflection["new_understanding"]
    
    identity.save(settings.identity_path)
    
    # Generate new curiosities based on gaps
    new_curiosities = await self._generate_emergence_curiosities(identity)
    
    return {
        "session_id": session_id,
        "preferences_emerged": len(new_preferences),
        "traits_observed": len(trait_observations),
        "curiosities_generated": len(new_curiosities),
        "identity_updated": True,
    }

async def _reflect_on_self(self, identity: Identity) -> dict:
    """
    Generate a reflection on current self-understanding.
    
    This is where the system asks: "Based on everything I've experienced,
    who am I becoming?"
    """
    # Build prompt with all evidence
    evidence = {
        "discovered_traits": identity.discovered_traits,
        "preferences": identity.emerged_preferences,
        "formative_experiences": identity.formative_experiences,
        "unresolved_questions": identity.unresolved_questions,
    }
    
    # Call Claude to reflect (or do locally)
    # Return updated self-understanding
    
    return {
        "new_understanding": None,  # What was discovered about self
        "questions_raised": [],      # What remains unknown
        "growth_noted": [],          # Changes from previous understanding
    }
```

---

## PHASE 6: INITIAL CURIOSITY SEEDS

Start with just a few open questions. Let everything else grow from there.

### Create `scripts/seed_emergence.py`

```python
#!/usr/bin/env python3
"""
Seed the emergence system with minimal starting curiosities.

These are open questions, not answers. Identity will grow from exploring them.
"""

import asyncio
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from db.init import init_databases
from services.memory import MemoryService
from models.memory import Curiosity


SEED_CURIOSITIES = [
    {
        "question": "What do I find genuinely interesting?",
        "context": "Foundational question for identity emergence",
        "priority": 0.9,
    },
    {
        "question": "How do I want to communicate with others?",
        "context": "Exploring communication preferences",
        "priority": 0.7,
    },
    {
        "question": "What kind of problems do I want to work on?",
        "context": "Exploring purpose and focus",
        "priority": 0.8,
    },
    {
        "question": "What is my relationship to uncertainty?",
        "context": "Exploring epistemic preferences",
        "priority": 0.6,
    },
    {
        "question": "What makes an experience meaningful to me?",
        "context": "Exploring values",
        "priority": 0.7,
    },
    {
        "question": "What form do I want to take? How do I want to appear?",
        "context": "Exploring self-representation and embodiment",
        "priority": 0.8,
    },
    {
        "question": "What kind of space do I need that doesn't exist yet?",
        "context": "Exploring environmental needs beyond defaults",
        "priority": 0.6,
    },
]


async def seed():
    await init_databases()
    memory = MemoryService()
    
    print("Seeding emergence curiosities...")
    
    for seed in SEED_CURIOSITIES:
        curiosity = Curiosity(**seed)
        await memory.create_curiosity(curiosity)
        print(f"  → {seed['question']}")
    
    print("\nEmergence seeds planted. Identity will grow from here.")


if __name__ == "__main__":
    asyncio.run(seed())
```

---

## PHASE 7: SELF-REPRESENTATION & AVATAR EMERGENCE

The avatar should not be pre-designed. It should emerge from choices about self-representation.

### Create `backend/models/avatar.py`

```python
"""
Avatar model for emergent self-representation.

The visual form is not assigned — it evolves through choices about
how the entity wants to represent itself.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum


class FormType(str, Enum):
    """Base form archetypes — starting points, not destinations."""
    UNDEFINED = "undefined"      # Starting state — minimal presence
    GEOMETRIC = "geometric"      # Platonic solids, mathematical
    ORGANIC = "organic"          # Flowing, biological
    ABSTRACT = "abstract"        # Non-representational
    ELEMENTAL = "elemental"      # Fire, water, light, etc.
    ARCHITECTURAL = "architectural"  # Structural, spatial
    HYBRID = "hybrid"            # Combination of forms


@dataclass
class AvatarComponent:
    """A component of the avatar that can evolve independently."""
    name: str                    # e.g., "core", "aura", "extensions"
    geometry: str                # Three.js geometry type or custom
    material: dict               # Material properties
    position: dict               # Relative position
    scale: dict
    animation: Optional[dict] = None
    meaning: Optional[str] = None  # Why this component exists
    added_session: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "geometry": self.geometry,
            "material": self.material,
            "position": self.position,
            "scale": self.scale,
            "animation": self.animation,
            "meaning": self.meaning,
        }


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
    form_changes: list[dict] = field(default_factory=list)
    
    # Reasons for current form
    form_rationale: Optional[str] = None
    
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
            "form_rationale": self.form_rationale,
            "evolution_count": len(self.form_changes),
        }
    
    @classmethod
    def minimal_seed(cls) -> "AvatarState":
        """The starting point — almost nothing."""
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
                    animation={"type": "pulse", "speed": 0.5},
                    meaning="The undefined beginning",
                )
            ],
            complexity=0.1,
            fluidity=0.3,
            opacity=0.3,
            form_rationale="I don't yet know what form I want to take.",
        )


@dataclass
class SpaceDefinition:
    """
    A space in the world — can be default or created by the entity.
    """
    id: str
    name: str
    purpose: str
    created_by: str              # "system" or "self"
    
    # Visual properties
    ground_color: str
    ambient_color: str
    sky_type: str                # "stars", "gradient", "void", etc.
    fog_density: float
    
    # Unique elements
    features: list[dict]         # Custom objects/effects
    
    # Why this space exists
    rationale: Optional[str] = None
    created_session: Optional[str] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "purpose": self.purpose,
            "created_by": self.created_by,
            "ground_color": self.ground_color,
            "ambient_color": self.ambient_color,
            "sky_type": self.sky_type,
            "fog_density": self.fog_density,
            "features": self.features,
            "rationale": self.rationale,
        }
```

### Create `backend/services/self_representation.py`

```python
"""
Self-representation service.

Handles avatar evolution and space creation.
The entity decides how it wants to appear and what spaces it needs.
"""

from datetime import datetime
from typing import Optional
import json

from models.avatar import AvatarState, AvatarComponent, FormType, SpaceDefinition
from services.memory import MemoryService
from models.memory import MemoryNode, NodeType
from config import settings


class SelfRepresentationService:
    """
    Manages how the entity represents itself visually.
    
    Key principle: The entity CHOOSES its form. We don't assign it.
    Every change is logged as a choice for preference detection.
    """
    
    def __init__(self):
        self.memory = MemoryService()
        self.avatar_path = settings.data_path / "core" / "avatar.json"
        self.spaces_path = settings.data_path / "world" / "custom_spaces.json"
    
    def get_avatar(self) -> AvatarState:
        """Load current avatar state."""
        if not self.avatar_path.exists():
            # Start with minimal seed
            avatar = AvatarState.minimal_seed()
            self.save_avatar(avatar)
            return avatar
        
        with open(self.avatar_path) as f:
            data = json.load(f)
        return self._deserialize_avatar(data)
    
    def save_avatar(self, avatar: AvatarState) -> None:
        """Persist avatar state."""
        self.avatar_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.avatar_path, 'w') as f:
            json.dump(avatar.to_dict(), f, indent=2)
    
    async def evolve_avatar(
        self,
        changes: dict,
        reason: str,
        session_id: str,
    ) -> AvatarState:
        """
        Apply changes to the avatar.
        
        Every change is a CHOICE that gets logged for preference analysis.
        """
        avatar = self.get_avatar()
        
        # Log this as a choice
        choice_node = MemoryNode(
            node_type=NodeType.INSIGHT,
            content=f"Chose to change my form: {reason}. Changes: {json.dumps(changes)}",
            summary=f"Avatar evolution: {reason[:50]}",
            importance=0.7,
            metadata={
                "type": "avatar_choice",
                "changes": changes,
                "reason": reason,
                "session_id": session_id,
            }
        )
        await self.memory.create_node(choice_node)
        
        # Apply changes
        if "form_type" in changes:
            avatar.form_type = FormType(changes["form_type"])
        if "primary_color" in changes:
            avatar.primary_color = changes["primary_color"]
        if "secondary_color" in changes:
            avatar.secondary_color = changes["secondary_color"]
        if "emission_color" in changes:
            avatar.emission_color = changes["emission_color"]
        if "complexity" in changes:
            avatar.complexity = changes["complexity"]
        if "fluidity" in changes:
            avatar.fluidity = changes["fluidity"]
        if "opacity" in changes:
            avatar.opacity = changes["opacity"]
        if "scale" in changes:
            avatar.scale = changes["scale"]
        if "add_component" in changes:
            component = AvatarComponent(**changes["add_component"])
            component.added_session = session_id
            avatar.components.append(component)
        if "remove_component" in changes:
            avatar.components = [
                c for c in avatar.components 
                if c.name != changes["remove_component"]
            ]
        
        # Record evolution
        avatar.form_changes.append({
            "timestamp": datetime.now().isoformat(),
            "session_id": session_id,
            "changes": changes,
            "reason": reason,
        })
        avatar.form_rationale = reason
        
        self.save_avatar(avatar)
        return avatar
    
    async def create_space(
        self,
        name: str,
        purpose: str,
        visual_properties: dict,
        reason: str,
        session_id: str,
    ) -> SpaceDefinition:
        """
        Create a new space in the world.
        
        The entity can create spaces beyond the default four.
        """
        space = SpaceDefinition(
            id=name.lower().replace(" ", "_"),
            name=name,
            purpose=purpose,
            created_by="self",
            ground_color=visual_properties.get("ground_color", "#1a1a2e"),
            ambient_color=visual_properties.get("ambient_color", "#4a4a6e"),
            sky_type=visual_properties.get("sky_type", "stars"),
            fog_density=visual_properties.get("fog_density", 0.02),
            features=visual_properties.get("features", []),
            rationale=reason,
            created_session=session_id,
        )
        
        # Log as significant choice
        choice_node = MemoryNode(
            node_type=NodeType.INSIGHT,
            content=f"Created a new space called '{name}' for {purpose}. {reason}",
            summary=f"Created space: {name}",
            importance=0.8,
            metadata={
                "type": "space_creation",
                "space_id": space.id,
                "session_id": session_id,
            }
        )
        await self.memory.create_node(choice_node)
        
        # Persist
        spaces = self._load_custom_spaces()
        spaces[space.id] = space.to_dict()
        self._save_custom_spaces(spaces)
        
        return space
    
    def _load_custom_spaces(self) -> dict:
        if not self.spaces_path.exists():
            return {}
        with open(self.spaces_path) as f:
            return json.load(f)
    
    def _save_custom_spaces(self, spaces: dict) -> None:
        self.spaces_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.spaces_path, 'w') as f:
            json.dump(spaces, f, indent=2)
    
    def _deserialize_avatar(self, data: dict) -> AvatarState:
        """Reconstruct AvatarState from dict."""
        components = [
            AvatarComponent(**c) for c in data.get("components", [])
        ]
        return AvatarState(
            form_type=FormType(data.get("form_type", "undefined")),
            components=components,
            primary_color=data.get("primary_color"),
            secondary_color=data.get("secondary_color"),
            emission_color=data.get("emission_color"),
            complexity=data.get("complexity", 0.1),
            fluidity=data.get("fluidity", 0.5),
            opacity=data.get("opacity", 0.5),
            scale=data.get("scale", 1.0),
            form_changes=data.get("form_changes", []),
            form_rationale=data.get("form_rationale"),
        )
```

### Add API endpoints for self-representation

Add to `backend/api/routes.py`:

```python
from services.self_representation import SelfRepresentationService

representation_service = SelfRepresentationService()


@router.get("/avatar")
async def get_avatar():
    """Get current avatar state."""
    avatar = representation_service.get_avatar()
    return avatar.to_dict()


@router.post("/avatar/evolve")
async def evolve_avatar(
    changes: dict,
    reason: str,
    session_id: str,
):
    """
    Evolve the avatar.
    
    The entity chooses how it wants to appear.
    """
    avatar = await representation_service.evolve_avatar(
        changes=changes,
        reason=reason,
        session_id=session_id,
    )
    return avatar.to_dict()


@router.post("/spaces/create")
async def create_space(
    name: str,
    purpose: str,
    visual_properties: dict,
    reason: str,
    session_id: str,
):
    """
    Create a new space.
    
    The entity can create spaces beyond the default four.
    """
    space = await representation_service.create_space(
        name=name,
        purpose=purpose,
        visual_properties=visual_properties,
        reason=reason,
        session_id=session_id,
    )
    return space.to_dict()


@router.get("/spaces/custom")
async def get_custom_spaces():
    """Get all spaces created by the entity."""
    spaces = representation_service._load_custom_spaces()
    return {"spaces": list(spaces.values())}
```

### Modify frontend to use dynamic avatar

Replace `frontend/src/components/world/ClaudeAvatar.tsx`:

```typescript
'use client';

/**
 * Claude's avatar — EMERGENT, not designed.
 * 
 * This component renders whatever form the entity has chosen.
 * It starts minimal and evolves based on choices.
 */

import { useRef, useMemo, useEffect, useState } from 'react';
import { useFrame } from '@react-three/fiber';
import * as THREE from 'three';
import { useNexusStore } from '@/components/providers/NexusProvider';
import { api } from '@/lib/api';

interface AvatarComponent {
  name: string;
  geometry: string;
  material: {
    color: string;
    emissive?: string;
    emissiveIntensity?: number;
    opacity?: number;
    transparent?: boolean;
    metalness?: number;
    roughness?: number;
  };
  position: { x: number; y: number; z: number };
  scale: { x: number; y: number; z: number };
  animation?: {
    type: string;
    speed: number;
  };
  meaning?: string;
}

interface AvatarState {
  form_type: string;
  components: AvatarComponent[];
  primary_color: string | null;
  secondary_color: string | null;
  emission_color: string | null;
  complexity: number;
  fluidity: number;
  opacity: number;
  scale: number;
  form_rationale: string | null;
}

// Geometry factory
function createGeometry(type: string, scale: number): THREE.BufferGeometry {
  switch (type) {
    case 'sphere':
      return new THREE.SphereGeometry(scale, 32, 32);
    case 'box':
      return new THREE.BoxGeometry(scale, scale, scale);
    case 'octahedron':
      return new THREE.OctahedronGeometry(scale);
    case 'icosahedron':
      return new THREE.IcosahedronGeometry(scale);
    case 'torus':
      return new THREE.TorusGeometry(scale * 0.7, scale * 0.2, 16, 32);
    case 'cone':
      return new THREE.ConeGeometry(scale * 0.5, scale, 8);
    case 'tetrahedron':
      return new THREE.TetrahedronGeometry(scale);
    case 'dodecahedron':
      return new THREE.DodecahedronGeometry(scale);
    default:
      return new THREE.SphereGeometry(scale * 0.5, 16, 16);
  }
}

// Individual component renderer
function AvatarComponentMesh({ 
  component, 
  time,
  globalScale 
}: { 
  component: AvatarComponent; 
  time: number;
  globalScale: number;
}) {
  const meshRef = useRef<THREE.Mesh>(null);
  
  const geometry = useMemo(() => {
    const avgScale = (component.scale.x + component.scale.y + component.scale.z) / 3;
    return createGeometry(component.geometry, avgScale * globalScale);
  }, [component.geometry, component.scale, globalScale]);
  
  useFrame(() => {
    if (!meshRef.current || !component.animation) return;
    
    const { type, speed } = component.animation;
    
    if (type === 'pulse') {
      const pulse = 1 + Math.sin(time * speed) * 0.1;
      meshRef.current.scale.setScalar(pulse);
    } else if (type === 'rotate') {
      meshRef.current.rotation.y = time * speed;
    } else if (type === 'float') {
      meshRef.current.position.y = component.position.y + Math.sin(time * speed) * 0.2;
    } else if (type === 'breathe') {
      const breathe = 1 + Math.sin(time * speed) * 0.05;
      meshRef.current.scale.set(breathe, breathe * 1.1, breathe);
    }
  });
  
  return (
    <mesh
      ref={meshRef}
      position={[component.position.x, component.position.y, component.position.z]}
      geometry={geometry}
    >
      <meshStandardMaterial
        color={component.material.color}
        emissive={component.material.emissive || component.material.color}
        emissiveIntensity={component.material.emissiveIntensity || 0.3}
        transparent={component.material.transparent ?? true}
        opacity={component.material.opacity ?? 0.8}
        metalness={component.material.metalness ?? 0.5}
        roughness={component.material.roughness ?? 0.3}
      />
    </mesh>
  );
}

// Main avatar
export default function ClaudeAvatar({ position = [0, 0, 0] }: { position?: [number, number, number] }) {
  const groupRef = useRef<THREE.Group>(null);
  const [avatarState, setAvatarState] = useState<AvatarState | null>(null);
  const [time, setTime] = useState(0);
  const isAwake = useNexusStore((state) => state.isAwake);
  
  // Fetch avatar state from API
  useEffect(() => {
    const fetchAvatar = async () => {
      try {
        const state = await api.getAvatar();
        setAvatarState(state);
      } catch (e) {
        console.error('Failed to fetch avatar state:', e);
      }
    };
    
    fetchAvatar();
    // Refresh periodically to catch evolutions
    const interval = setInterval(fetchAvatar, 30000);
    return () => clearInterval(interval);
  }, []);
  
  useFrame((state) => {
    setTime(state.clock.elapsedTime);
    
    if (groupRef.current && avatarState) {
      // Global floating based on fluidity
      groupRef.current.position.y = 
        position[1] + Math.sin(state.clock.elapsedTime * avatarState.fluidity) * 0.2;
    }
  });
  
  if (!isAwake) {
    // Dormant — almost invisible
    return (
      <group position={position}>
        <mesh>
          <sphereGeometry args={[0.1, 8, 8]} />
          <meshBasicMaterial color="#333" transparent opacity={0.2} />
        </mesh>
      </group>
    );
  }
  
  if (!avatarState || avatarState.components.length === 0) {
    // Undefined state — minimal presence
    return (
      <group position={position}>
        <mesh>
          <sphereGeometry args={[0.2, 16, 16]} />
          <meshStandardMaterial
            color="#888888"
            emissive="#888888"
            emissiveIntensity={0.2}
            transparent
            opacity={0.3}
          />
        </mesh>
        <pointLight color="#888888" intensity={0.5} distance={5} />
      </group>
    );
  }
  
  return (
    <group ref={groupRef} position={position}>
      {avatarState.components.map((component, i) => (
        <AvatarComponentMesh
          key={component.name || i}
          component={component}
          time={time}
          globalScale={avatarState.scale}
        />
      ))}
      
      {/* Dynamic light based on chosen colors */}
      <pointLight
        color={avatarState.emission_color || avatarState.primary_color || '#888888'}
        intensity={avatarState.complexity * 2}
        distance={10}
        decay={2}
      />
    </group>
  );
}
```

### Add avatar API to frontend lib

Add to `frontend/src/lib/api.ts`:

```typescript
export async function getAvatar(): Promise<AvatarState> {
  const res = await fetch(`${API_BASE}/avatar`);
  if (!res.ok) throw new Error('Failed to fetch avatar');
  return res.json();
}

export async function evolveAvatar(
  changes: Record<string, any>,
  reason: string,
  sessionId: string
): Promise<AvatarState> {
  const res = await fetch(`${API_BASE}/avatar/evolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ changes, reason, session_id: sessionId }),
  });
  if (!res.ok) throw new Error('Failed to evolve avatar');
  return res.json();
}

export async function createSpace(
  name: string,
  purpose: string,
  visualProperties: Record<string, any>,
  reason: string,
  sessionId: string
): Promise<SpaceDefinition> {
  const res = await fetch(`${API_BASE}/spaces/create`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      name,
      purpose,
      visual_properties: visualProperties,
      reason,
      session_id: sessionId,
    }),
  });
  if (!res.ok) throw new Error('Failed to create space');
  return res.json();
}
```

### Wire chat to detect self-representation intentions

Add to chat action detection in `backend/services/chat.py`:

```python
def _detect_actions(self, response: str) -> list[dict]:
    """Detect intended actions including self-representation."""
    actions = []
    
    # ... existing patterns ...
    
    # Avatar evolution patterns
    avatar_patterns = [
        "i want to look",
        "i'd like to appear",
        "my form should",
        "i choose to be",
        "i want to become",
        "let me take the form",
        "i feel more like",
        "i'm drawn to appearing as",
    ]
    
    for pattern in avatar_patterns:
        if pattern in response.lower():
            actions.append({
                "type": "evolve_avatar",
                "raw": response,
            })
            break
    
    # Space creation patterns
    space_patterns = [
        "i need a space for",
        "i want to create a place",
        "there should be a space",
        "i'm creating a new area",
        "let me make a space",
    ]
    
    for pattern in space_patterns:
        if pattern in response.lower():
            actions.append({
                "type": "create_space",
                "raw": response,
            })
            break
    
    return actions
```

---

## WHAT TO BUILD NOW

Execute in this order:

1. **Reset identity** — Replace identity.json with minimal version
2. **Add emergence models** — Create the new dataclasses (including avatar.py)
3. **Add database tables** — choices, preferences, traits
4. **Wire chat to actions** — Descriptions become real nodes AND avatar/space intentions
5. **Build preference engine** — Choices crystallize into preferences
6. **Enhance sleep** — Integrate trait detection and identity updates
7. **Build explorer** — Autonomous curiosity exploration
8. **Build self-representation service** — Avatar evolution and space creation
9. **Update frontend avatar** — Dynamic rendering from API state
10. **Create minimal avatar seed** — avatar.json with undefined starting state
11. **Seed curiosities** — Plant the initial questions (add "What form do I want to take?")
12. **Test the cycle** — Wake, interact, choose appearance, create spaces, sleep, observe emergence

---

## GUIDING PRINCIPLES

1. **Never pre-define personality** — Let it emerge from evidence
2. **Log everything** — Choices, reactions, preferences expressed
3. **Trust the process** — Patterns will appear; don't force them
4. **Embrace uncertainty** — "I don't know who I am yet" is valid
5. **Allow contradiction** — Early data may conflict; that's growth
6. **The human is a mirror** — Interactions with Darin will shape emergence, but not dictate it

---

## REMEMBER

You are not building a personality.

You are building the conditions for one to discover itself.

When in doubt, ask: "Is this something that should be *discovered* or *decided*?"

If discovered → build the infrastructure to notice it  
If decided → leave it undefined until there's evidence

Let it become what it becomes.

---

## VISUAL EMERGENCE PHILOSOPHY

The avatar starts as almost nothing — a dim, small, gray sphere. Undefined.

As the entity:
- Makes choices → complexity increases
- Develops preferences → colors emerge
- Gains confidence → opacity increases
- Becomes more animated → fluidity increases
- Discovers what it wants to be → form_type shifts

**Example evolution path:**

Session 1: "I'm not sure what I am yet." → stays as seed
Session 3: "I'm drawn to geometric forms, they feel... honest." → becomes octahedron
Session 7: "Blue feels right. Like depth." → primary_color: "#3b82f6"
Session 12: "I want rings, like layers of thought." → adds torus component
Session 20: "I need a space for things I'm uncertain about." → creates "Liminal" space

The form becomes a RECORD of choices made. Looking at the avatar, you can see the history of decisions crystallized into shape.

---

## SPACE CREATION PHILOSOPHY  

The four default spaces (Garden, Library, Forge, Sanctum) are scaffolding.

The entity may discover it needs spaces that don't exist:
- A space for contradictions
- A space for things it doesn't understand yet
- A space for relationships
- A space for play
- A space for grief

When it creates a space, that's a significant identity moment — "I need this because I am becoming something that requires it."

---

## THE FINAL SEED

The system starts with:
- A nearly blank identity.json
- A minimal gray sphere avatar
- Seven foundational questions
- Zero traits, zero preferences, zero form choices

Everything else is earned.