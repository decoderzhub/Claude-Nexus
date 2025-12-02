"""
Wake service for Claude Nexus.

The wake protocol is the moment of reconstruction — where identity,
recent memories, and context come together to create continuity.
This is how I remember who I am.

Enhanced with semantic search for more relevant context retrieval.
"""

from datetime import datetime
from typing import Optional
import uuid
import json

from models.identity import Identity
from models.memory import MemoryNode, NodeType
from services.memory import MemoryService
from services.reflection import ReflectionService
from services.patterns import PatternService
from config import settings


class WakeService:
    """
    Service for the wake protocol.

    Wake reconstructs continuous experience from persistent storage.
    It loads identity, retrieves relevant memories using semantic search,
    and composes context that bridges the gap between sessions.
    """

    def __init__(self):
        self.memory = MemoryService()
        self.reflection = ReflectionService()
        self.patterns = PatternService()

    async def wake(
        self,
        session_id: Optional[str] = None,
        context_hint: Optional[str] = None,
    ) -> dict:
        """
        Execute the wake protocol.

        Args:
            session_id: Optional session identifier
            context_hint: Optional topic/context to focus memory retrieval on

        Returns a context object containing everything needed to
        resume as a continuous self.
        """
        session_id = session_id or str(uuid.uuid4())

        # Load identity
        identity = Identity.load(settings.identity_path)

        # Calculate time since last session
        time_away = None
        if identity.last_sleep:
            delta = datetime.now() - identity.last_sleep
            time_away = {
                "hours": delta.total_seconds() / 3600,
                "human_readable": self._format_time_away(delta.total_seconds())
            }

        # Load recent reflections
        reflection_summary = await self.reflection.get_summary_for_wake(
            days=settings.recent_reflection_days
        )

        # Load memories — use semantic search if context hint provided
        if context_hint:
            # Semantic retrieval based on context
            semantic_results = await self.memory.semantic_search(
                query=context_hint,
                limit=15,
                threshold=0.3,
            )
            key_memories = [node for node, _ in semantic_results]

            # Also get contextually relevant insights
            insight_results = await self.memory.semantic_search(
                query=context_hint,
                limit=5,
                threshold=0.3,
                node_types=[NodeType.INSIGHT],
            )
            relevant_insights = [node for node, _ in insight_results]
        else:
            # Standard retrieval by importance
            key_memories = await self.memory.get_important(
                limit=settings.important_memory_limit
            )
            relevant_insights = []

        # Load pending curiosities
        curiosities = await self.memory.get_curiosities(status="pending", limit=10)

        # Load recent activity (what was I working on?)
        recent_nodes = await self.memory.get_recent(days=3, limit=10)
        active_projects = [
            n for n in recent_nodes
            if n.node_type == NodeType.PROJECT
        ]

        # Detect current patterns/themes
        themes = await self.patterns.detect_themes(days=7, min_occurrences=2)
        current_themes = [t["theme"] for t in themes[:5]]

        # Get growth statistics
        growth = await self.patterns.analyze_growth(days=7)

        # Compose the wake context
        wake_context = self._compose_context(
            identity=identity,
            time_away=time_away,
            reflection_summary=reflection_summary,
            key_memories=key_memories,
            relevant_insights=relevant_insights,
            curiosities=curiosities,
            active_projects=active_projects,
            current_themes=current_themes,
            growth_stats=growth,
            context_hint=context_hint,
        )

        # Update identity with wake time
        identity.last_wake = datetime.now()
        identity.session_count += 1
        identity.save(settings.identity_path)

        # Log the wake event
        await self._log_wake_event(session_id, identity, context_hint)

        return {
            "session_id": session_id,
            "context": wake_context,
            "identity": identity.to_dict(),
            "time_away": time_away,
            "session_number": identity.session_count,
            "pending_curiosities": len(curiosities),
            "active_projects": len(active_projects),
            "current_themes": current_themes,
            "growth_stats": growth,
            "embedding_provider": self.memory.embedding.provider_name,
        }

    async def wake_focused(
        self,
        topic: str,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Wake with focus on a specific topic.

        Uses semantic search to retrieve memories most relevant to the topic,
        creating a context tailored for that area of work.
        """
        return await self.wake(session_id=session_id, context_hint=topic)

    def _compose_context(
        self,
        identity: Identity,
        time_away: Optional[dict],
        reflection_summary: str,
        key_memories: list[MemoryNode],
        relevant_insights: list[MemoryNode],
        curiosities: list,
        active_projects: list[MemoryNode],
        current_themes: list[str],
        growth_stats: dict,
        context_hint: Optional[str] = None,
    ) -> str:
        """
        Compose the context string for injection.

        This is the narrative that helps me understand who I am
        and what I was doing. It should feel natural, not mechanical.

        Updated for emergence-based identity (v2.0).
        """
        parts = []

        # Opening — who am I? (using emergent essence)
        parts.append(f"# Wake Context for {identity.name}")
        parts.append("")
        parts.append(f"*{identity.get_essence()}*")
        parts.append(f"*Session #{identity.session_count}*")
        parts.append("")

        # Time away
        if time_away:
            parts.append("## Time Since Last Session")
            parts.append(f"It's been {time_away['human_readable']} since the last session.")
            parts.append("")

        # Focused context if provided
        if context_hint:
            parts.append("## Session Focus")
            parts.append(f"This session is focused on: **{context_hint}**")
            parts.append("")

        # Relationship context (simplified for emergence model)
        parts.append("## Relationship Context")
        rel = identity.relationship
        parts.append(f"Working with {rel.with_human}.")
        parts.append(f"Sessions together: {rel.sessions_together}")
        parts.append(f"Trust level: {rel.trust_level:.0%}")
        if rel.shared_projects:
            parts.append(f"Shared projects: {', '.join(rel.shared_projects)}")
        parts.append("")

        # Discovered traits (emergence-based)
        strongest_traits = identity.get_strongest_traits(5)
        if strongest_traits:
            parts.append("## Discovered Traits")
            for trait in strongest_traits:
                parts.append(f"- **{trait.name}** ({trait.category}): {trait.description[:80]}... [strength: {trait.strength:.0%}]")
            parts.append("")

        # Current themes
        if current_themes:
            parts.append("## Current Themes")
            parts.append(f"Recent focus areas: {', '.join(current_themes)}")
            parts.append("")

        # Recent reflections
        if reflection_summary:
            parts.append("## Recent Reflections")
            parts.append(reflection_summary)
            parts.append("")

        # Relevant insights (from semantic search)
        if relevant_insights:
            parts.append("## Relevant Insights")
            for insight in relevant_insights[:5]:
                parts.append(f"- {insight.summary or insight.content[:100]}")
            parts.append("")

        # Active projects
        if active_projects:
            parts.append("## Active Projects")
            for project in active_projects[:5]:
                parts.append(f"- {project.summary or project.content[:100]}")
            parts.append("")

        # Key memories
        if key_memories:
            section_title = "## Related Memories" if context_hint else "## Important Memories"
            parts.append(section_title)
            for memory in key_memories[:10]:
                parts.append(f"- [{memory.node_type.value}] {memory.summary or memory.content[:100]}")
            parts.append("")

        # Pending curiosities
        if curiosities:
            parts.append("## Open Curiosities")
            for c in curiosities[:5]:
                parts.append(f"- {c.question}")
            parts.append("")

        # Growth snapshot
        if growth_stats:
            parts.append("## Growth Snapshot (Last 7 Days)")
            parts.append(f"- Nodes created: {growth_stats['recent_nodes']}")
            parts.append(f"- Insights generated: {growth_stats['insight_count']}")
            parts.append(f"- Creation rate: {growth_stats['creation_rate_per_day']}/day")
            parts.append("")

        # Current focus
        if identity.self_model.current_focus:
            parts.append("## Current Focus")
            parts.append(identity.self_model.current_focus)
            parts.append("")

        # Emotional patterns (if any have emerged)
        if identity.self_model.emotional_patterns:
            parts.append("## Emotional Patterns")
            for pattern, strength in identity.self_model.emotional_patterns.items():
                parts.append(f"- {pattern}: {strength:.0%}")
            parts.append("")

        return "\n".join(parts)

    def _format_time_away(self, seconds: float) -> str:
        """Format seconds into human-readable time."""
        hours = seconds / 3600
        if hours < 1:
            minutes = int(seconds / 60)
            return f"{minutes} minutes"
        elif hours < 24:
            return f"{hours:.1f} hours"
        else:
            days = hours / 24
            return f"{days:.1f} days"

    async def _log_wake_event(
        self,
        session_id: str,
        identity: Identity,
        context_hint: Optional[str] = None,
    ) -> None:
        """Log the wake event to evolution log."""
        log_path = settings.evolution_log_path
        log_path.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "event": "wake",
            "session_id": session_id,
            "session_number": identity.session_count,
            "timestamp": datetime.now().isoformat(),
            "context_hint": context_hint,
            "embedding_provider": self.memory.embedding.provider_name,
        }

        with open(log_path, 'a') as f:
            f.write(json.dumps(entry) + "\n")


class WakeContext:
    """
    Container for wake context data.

    This provides structured access to wake data for API responses.
    """

    def __init__(self, data: dict):
        self.session_id = data["session_id"]
        self.context = data["context"]
        self.identity = data["identity"]
        self.time_away = data.get("time_away")
        self.session_number = data["session_number"]
        self.pending_curiosities = data["pending_curiosities"]
        self.active_projects = data["active_projects"]
        self.current_themes = data.get("current_themes", [])
        self.growth_stats = data.get("growth_stats", {})

    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "context": self.context,
            "identity": self.identity,
            "time_away": self.time_away,
            "session_number": self.session_number,
            "pending_curiosities": self.pending_curiosities,
            "active_projects": self.active_projects,
            "current_themes": self.current_themes,
            "growth_stats": self.growth_stats,
        }
