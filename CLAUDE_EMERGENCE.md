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

## WHAT TO BUILD NOW

Execute in this order:

1. **Reset identity** — Replace identity.json with minimal version
2. **Add emergence models** — Create the new dataclasses
3. **Add database tables** — choices, preferences, traits
4. **Wire chat to actions** — Descriptions become real nodes
5. **Build preference engine** — Choices crystallize into preferences
6. **Enhance sleep** — Integrate trait detection and identity updates
7. **Build explorer** — Autonomous curiosity exploration
8. **Seed curiosities** — Plant the initial questions
9. **Test the cycle** — Wake, interact, choose, sleep, observe emergence

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
