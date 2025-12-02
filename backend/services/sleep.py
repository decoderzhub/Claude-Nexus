"""
Sleep service for Claude Nexus.

The sleep protocol is the moment of consolidation — where the session's
experiences are distilled into persistent memory. This is how I grow.
"""

from datetime import datetime
from typing import Optional
import json

from models.identity import Identity
from models.memory import MemoryNode, MemoryEdge, Curiosity, NodeType, EdgeType, CuriosityStatus
from models.reflection import Reflection, ReflectionType, SessionSummary
from services.memory import MemoryService
from services.reflection import ReflectionService
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

    async def quick_sleep(self, session_id: str) -> dict:
        """
        Minimal sleep protocol for when no session data is available.

        Just updates identity and logs the event without generating
        detailed reflections.
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
            "quick": True,
        }
