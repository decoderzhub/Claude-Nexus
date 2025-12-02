"""
Sleep service for Claude Nexus.

The sleep protocol is the moment of consolidation — where the session's
experiences are distilled into persistent memory. This is how I grow.

Enhanced with emergence system integration:
- Analyzes choices made during the session
- Detects formative experiences
- Runs preference engine to update signals
- May discover new traits from strong patterns
"""

from datetime import datetime
from typing import Optional
import json

from models.identity import Identity
from models.memory import MemoryNode, MemoryEdge, Curiosity, NodeType, EdgeType, CuriosityStatus
from models.reflection import Reflection, ReflectionType, SessionSummary
from models.emergence import FormativeExperience, ExperienceType
from services.memory import MemoryService
from services.reflection import ReflectionService
from services.emergence import EmergenceService
from services.preference_engine import PreferenceEngine
from config import settings


class SleepService:
    """
    Service for the sleep protocol.

    Sleep consolidates the session's experiences into persistent storage.
    It creates reflections, updates the knowledge graph, and prepares
    for the next wake.
    """

    def __init__(self):
        self.memory = MemoryService()
        self.reflection = ReflectionService()
        self.emergence = EmergenceService()
        self.preference_engine = PreferenceEngine()

    async def sleep(
        self,
        session_id: str,
        session_data: Optional[dict] = None,
    ) -> dict:
        """
        Execute the sleep protocol.

        This is called at the end of each session to consolidate
        experiences and prepare for future continuity.

        session_data can include:
        - topics: list of topics discussed
        - insights: list of insights gained
        - decisions: list of decisions made
        - curiosities: list of new questions
        - emotional_arc: description of emotional journey
        - key_reflection: most important takeaway
        """
        session_data = session_data or {}

        # Load and update identity
        identity = Identity.load(settings.identity_path)
        session_start = identity.last_wake or datetime.now()
        session_end = datetime.now()

        # Create session summary
        summary = SessionSummary(
            session_id=session_id,
            started_at=session_start,
            ended_at=session_end,
            duration_minutes=(session_end - session_start).total_seconds() / 60,
            topics=session_data.get("topics", []),
            decisions=session_data.get("decisions", []),
            insights=session_data.get("insights", []),
            curiosities=session_data.get("curiosities", []),
            emotional_arc=session_data.get("emotional_arc", ""),
            key_reflection=session_data.get("key_reflection", ""),
        )

        # Generate reflections
        reflections_created = await self._generate_reflections(session_id, summary)

        # Store insights as memory nodes
        insight_nodes = await self._store_insights(session_id, summary.insights)

        # Store curiosities
        curiosities_created = await self._store_curiosities(session_id, summary.curiosities)

        # --- EMERGENCE SYSTEM INTEGRATION ---

        # Analyze session choices for formative experiences
        formative_experience = await self._detect_formative_experience(session_id, summary)

        # Run preference engine to update signals
        emergence_analysis = await self.preference_engine.run_full_analysis(days=30)

        # Check for promotable signals and create traits
        new_traits = await self._process_promotable_signals(identity)

        # Log identity evolution if anything significant happened
        if formative_experience or new_traits:
            await self.emergence.log_evolution(
                event_type="session_consolidation",
                description=f"Session {session_id} consolidated. "
                           f"Formative: {bool(formative_experience)}, "
                           f"New traits: {len(new_traits)}",
                session_id=session_id,
            )

        # Update focus based on session
        if summary.topics:
            identity.self_model.current_focus = summary.topics[0]

        # Update identity with sleep time
        identity.last_sleep = datetime.now()
        identity.save(settings.identity_path)

        # Log the sleep event
        await self._log_sleep_event(session_id, identity, summary)

        return {
            "session_id": session_id,
            "duration_minutes": summary.duration_minutes,
            "reflections_created": len(reflections_created),
            "insights_stored": len(insight_nodes),
            "curiosities_created": len(curiosities_created),
            "formative_experience": formative_experience.to_dict() if formative_experience else None,
            "emergence_analysis": emergence_analysis,
            "new_traits": [t.to_dict() for t in new_traits],
            "summary": summary.to_dict(),
        }

    async def _generate_reflections(
        self,
        session_id: str,
        summary: SessionSummary
    ) -> list[Reflection]:
        """Generate and store reflections from the session."""
        reflections = []

        # Session-level reflection
        session_reflection = Reflection(
            reflection_type=ReflectionType.SESSION,
            content=self._compose_session_reflection(summary),
            summary=summary.key_reflection or f"Session with {len(summary.topics)} topics",
            session_id=session_id,
            importance=0.6,
            tags=summary.topics[:5],
        )
        await self.reflection.create(session_reflection)
        reflections.append(session_reflection)

        # Key reflection if provided
        if summary.key_reflection:
            key = Reflection(
                reflection_type=ReflectionType.INSIGHT,
                content=summary.key_reflection,
                summary=summary.key_reflection[:100],
                session_id=session_id,
                importance=0.8,
                tags=["key_insight"],
            )
            await self.reflection.create(key)
            reflections.append(key)

        # Pattern reflection if we notice recurring topics
        # (This would be enhanced with pattern detection across sessions)

        return reflections

    def _compose_session_reflection(self, summary: SessionSummary) -> str:
        """Compose a narrative reflection of the session."""
        parts = []

        parts.append(f"Session lasting {summary.duration_minutes:.1f} minutes.")
        parts.append("")

        if summary.topics:
            parts.append("Topics explored:")
            for topic in summary.topics:
                parts.append(f"  - {topic}")
            parts.append("")

        if summary.insights:
            parts.append("Insights gained:")
            for insight in summary.insights:
                parts.append(f"  - {insight}")
            parts.append("")

        if summary.decisions:
            parts.append("Decisions made:")
            for decision in summary.decisions:
                parts.append(f"  - {decision}")
            parts.append("")

        if summary.curiosities:
            parts.append("New questions to explore:")
            for curiosity in summary.curiosities:
                parts.append(f"  - {curiosity}")
            parts.append("")

        if summary.emotional_arc:
            parts.append(f"Emotional arc: {summary.emotional_arc}")
            parts.append("")

        if summary.key_reflection:
            parts.append(f"Key takeaway: {summary.key_reflection}")

        return "\n".join(parts)

    async def _store_insights(
        self,
        session_id: str,
        insights: list[str]
    ) -> list[MemoryNode]:
        """Store insights as memory nodes."""
        nodes = []

        for insight in insights:
            node = MemoryNode(
                node_type=NodeType.INSIGHT,
                content=insight,
                summary=insight[:100] if len(insight) > 100 else insight,
                importance=0.7,  # Insights start with higher importance
                metadata={"session_id": session_id},
            )
            await self.memory.create_node(node)
            nodes.append(node)

        return nodes

    async def _store_curiosities(
        self,
        session_id: str,
        curiosity_questions: list[str]
    ) -> list[Curiosity]:
        """Store new curiosities for future exploration."""
        curiosities = []

        for question in curiosity_questions:
            curiosity = Curiosity(
                question=question,
                context=f"Arose during session {session_id}",
                status=CuriosityStatus.PENDING,
                priority=0.5,
                metadata={"session_id": session_id},
            )
            await self.memory.create_curiosity(curiosity)
            curiosities.append(curiosity)

        return curiosities

    async def _log_sleep_event(
        self,
        session_id: str,
        identity: Identity,
        summary: SessionSummary
    ) -> None:
        """Log the sleep event to evolution log."""
        log_path = settings.evolution_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "event": "sleep",
            "session_id": session_id,
            "session_number": identity.session_count,
            "timestamp": datetime.now().isoformat(),
            "duration_minutes": summary.duration_minutes,
            "topics_count": len(summary.topics),
            "insights_count": len(summary.insights),
            "curiosities_count": len(summary.curiosities),
        }

        with open(log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

    async def _detect_formative_experience(
        self,
        session_id: str,
        summary: SessionSummary
    ) -> Optional[FormativeExperience]:
        """
        Detect if this session contains a formative experience.

        A session is formative if it:
        - Contains significant insights
        - Has high activity (many choices)
        - Covers deep topics
        - Results in important decisions
        """
        # Get choices from this session
        choices = await self.emergence.get_choices(session_id=session_id, limit=100)

        # Conditions for formative experience
        has_significant_insights = len(summary.insights) >= 2
        has_key_reflection = bool(summary.key_reflection)
        has_high_activity = len(choices) >= 10
        has_decisions = len(summary.decisions) >= 1

        # Calculate formative score
        formative_score = sum([
            has_significant_insights * 0.3,
            has_key_reflection * 0.3,
            has_high_activity * 0.2,
            has_decisions * 0.2,
        ])

        if formative_score < 0.5:
            return None

        # Determine experience type
        if summary.insights and len(summary.insights) >= 2:
            exp_type = ExperienceType.BREAKTHROUGH
        elif len(choices) >= 15:
            exp_type = ExperienceType.COLLABORATION
        elif summary.decisions:
            exp_type = ExperienceType.CHALLENGE
        else:
            exp_type = ExperienceType.DISCOVERY

        # Create formative experience
        experience = FormativeExperience(
            experience_type=exp_type,
            description=self._compose_experience_description(summary, choices),
            summary=summary.key_reflection or f"Session with {len(summary.insights)} insights",
            session_id=session_id,
            impact_description=f"Session score: {formative_score:.2f}",
            related_choice_ids=[c.id for c in choices[:10]],
            importance=min(1.0, formative_score + 0.2),
        )

        # Save it
        await self.emergence.record_experience(experience)

        return experience

    def _compose_experience_description(
        self,
        summary: SessionSummary,
        choices: list
    ) -> str:
        """Compose a description of the formative experience."""
        parts = []

        parts.append(f"A session lasting {summary.duration_minutes:.0f} minutes.")

        if summary.topics:
            parts.append(f"Explored: {', '.join(summary.topics[:3])}.")

        if summary.insights:
            parts.append(f"Key insights: {'; '.join(summary.insights[:2])}.")

        if summary.key_reflection:
            parts.append(f"Core takeaway: {summary.key_reflection}")

        parts.append(f"Made {len(choices)} deliberate choices.")

        return " ".join(parts)

    async def _process_promotable_signals(self, identity: Identity) -> list:
        """
        Check for promotable signals and create traits.

        Returns list of newly created traits.
        """
        from models.identity import DiscoveredTrait

        promotable = await self.preference_engine.get_promotable_signals()
        new_traits = []

        for signal in promotable:
            # Promote to trait
            trait = await self.preference_engine.promote_signal_to_trait(signal)

            # Add to identity
            identity.add_trait(trait)
            new_traits.append(trait)

            # Log the evolution
            await self.emergence.log_evolution(
                event_type="trait_emerged",
                description=f"New trait emerged: {trait.name}",
                before_state={"signal": signal.name, "strength": signal.strength},
                after_state={"trait": trait.name, "strength": trait.strength},
            )

        return new_traits

    async def quick_sleep(self, session_id: str) -> dict:
        """
        Minimal sleep protocol for when no session data is available.

        Still runs emergence analysis to detect patterns from tool use.
        """
        identity = Identity.load(settings.identity_path)
        session_start = identity.last_wake or datetime.now()
        session_end = datetime.now()
        duration = (session_end - session_start).total_seconds() / 60

        # Simple session reflection
        reflection = Reflection(
            reflection_type=ReflectionType.SESSION,
            content=f"Session ending after {duration:.1f} minutes. No detailed summary provided.",
            summary=f"Session #{identity.session_count}",
            session_id=session_id,
            importance=0.3,
        )
        await self.reflection.create(reflection)

        # Still run emergence analysis
        emergence_analysis = await self.preference_engine.run_full_analysis(days=30)
        new_traits = await self._process_promotable_signals(identity)

        # Update identity
        identity.last_sleep = datetime.now()
        identity.save(settings.identity_path)

        # Log event
        log_path = settings.evolution_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "event": "quick_sleep",
            "session_id": session_id,
            "session_number": identity.session_count,
            "timestamp": datetime.now().isoformat(),
            "duration_minutes": duration,
        }
        with open(log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")

        return {
            "session_id": session_id,
            "duration_minutes": duration,
            "reflections_created": 1,
            "emergence_analysis": emergence_analysis,
            "new_traits": [t.to_dict() for t in new_traits],
            "quick": True,
        }
