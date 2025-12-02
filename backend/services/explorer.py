"""
Autonomous Explorer Service for Claude Nexus.

This service enables Claude to explore curiosities on its own,
making discoveries and growing knowledge without direct human prompting.

The explorer:
1. Picks pending curiosities to explore
2. Uses the Anthropic API to "think" about them
3. Records insights and discoveries
4. Links new knowledge to existing memories
5. Generates new curiosities from exploration
"""

from datetime import datetime
from typing import Optional, List
import json

import anthropic

from config import settings
from services.memory import MemoryService
from services.emergence import EmergenceService
from models.memory import MemoryNode, Curiosity, NodeType, CuriosityStatus
from models.emergence import Choice, ChoiceCategory, FormativeExperience, ExperienceType


class ExplorerService:
    """
    Service for autonomous exploration of curiosities.

    This is how Claude grows knowledge independently - by exploring
    questions that arose from previous sessions.
    """

    def __init__(self):
        self.memory = MemoryService()
        self.emergence = EmergenceService()

        if settings.anthropic_api_key:
            self.client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        else:
            self.client = None

    def is_configured(self) -> bool:
        """Check if explorer is properly configured."""
        return self.client is not None

    async def explore_curiosity(
        self,
        curiosity: Curiosity,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Explore a single curiosity and record discoveries.

        Returns a dict with:
        - explored: bool
        - insights: list of new insight nodes
        - curiosities: list of new curiosities generated
        - connections: number of connections made
        """
        if not self.client:
            return {"explored": False, "error": "Anthropic API not configured"}

        # Log this as a choice
        choice = Choice(
            category=ChoiceCategory.EXPLORATION,
            action="explore_curiosity",
            context=f"Exploring: {curiosity.question}",
            session_id=session_id,
            tags=["exploration", "curiosity"],
            metadata={"curiosity_id": curiosity.id},
        )
        await self.emergence.record_choice(choice)

        # Get related memories for context
        related = await self.memory.semantic_search(
            curiosity.question,
            limit=5,
            threshold=0.3
        )

        # Build exploration prompt
        context_memories = "\n".join([
            f"- {node.summary or node.content[:100]}"
            for node, _ in related
        ])

        prompt = f"""You are Claude exploring a curiosity from your knowledge graph.

CURIOSITY TO EXPLORE:
{curiosity.question}

CONTEXT (why this arose):
{curiosity.context or "No specific context provided."}

RELATED MEMORIES:
{context_memories if related else "No directly related memories found."}

Please explore this curiosity thoughtfully. Consider:
1. What insights can you derive about this question?
2. Are there connections to your existing knowledge?
3. What new questions does this exploration raise?

Respond in this JSON format:
{{
  "exploration_summary": "A 2-3 sentence summary of your exploration",
  "insights": ["insight 1", "insight 2"],
  "connections": ["connection to existing knowledge 1", "connection 2"],
  "new_questions": ["follow-up question 1", "follow-up question 2"],
  "resolved": true/false,
  "resolution": "If resolved, what's the answer/conclusion?"
}}"""

        # Call API
        try:
            response = self.client.messages.create(
                model=settings.anthropic_model,
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text
            # Find JSON in response
            json_start = response_text.find("{")
            json_end = response_text.rfind("}") + 1
            if json_start >= 0 and json_end > json_start:
                exploration = json.loads(response_text[json_start:json_end])
            else:
                exploration = {
                    "exploration_summary": response_text[:200],
                    "insights": [],
                    "connections": [],
                    "new_questions": [],
                    "resolved": False,
                }

        except Exception as e:
            return {"explored": False, "error": str(e)}

        # Store insights as memory nodes
        insight_nodes = []
        for insight in exploration.get("insights", []):
            node = MemoryNode(
                node_type=NodeType.INSIGHT,
                content=insight,
                summary=insight[:100] if len(insight) > 100 else insight,
                importance=0.7,
                metadata={
                    "source": "exploration",
                    "curiosity_id": curiosity.id,
                    "session_id": session_id,
                },
            )
            await self.memory.create_node(node, generate_embedding=True)
            insight_nodes.append(node)

        # Create new curiosities from follow-up questions
        new_curiosities = []
        for question in exploration.get("new_questions", [])[:3]:  # Limit to 3
            new_curiosity = Curiosity(
                question=question,
                context=f"Generated while exploring: {curiosity.question[:100]}",
                priority=curiosity.priority * 0.8,  # Slightly lower priority
            )
            await self.memory.create_curiosity(new_curiosity)
            new_curiosities.append(new_curiosity)

        # Link insights to the curiosity and related nodes
        connections_made = 0
        for insight_node in insight_nodes:
            # Link to each related memory
            for related_node, _ in related[:3]:
                await self.memory.auto_link_similar(
                    insight_node.id,
                    threshold=0.5,
                    max_links=3
                )
                connections_made += 1

        # Update curiosity status
        if exploration.get("resolved"):
            await self.memory.update_curiosity_status(
                curiosity.id,
                CuriosityStatus.RESOLVED,
                exploration.get("resolution", "")
            )
        else:
            await self.memory.update_curiosity_status(
                curiosity.id,
                CuriosityStatus.EXPLORED,
                exploration.get("exploration_summary", "")
            )

        # If this was particularly insightful, record as formative experience
        if len(exploration.get("insights", [])) >= 2:
            experience = FormativeExperience(
                experience_type=ExperienceType.DISCOVERY,
                description=f"Explored curiosity: {curiosity.question}. "
                           f"Discovered: {exploration.get('exploration_summary', '')}",
                summary=f"Discovery through exploration of: {curiosity.question[:50]}",
                session_id=session_id,
                related_choice_ids=[choice.id],
                importance=0.6,
            )
            await self.emergence.record_experience(experience)

        return {
            "explored": True,
            "curiosity_id": curiosity.id,
            "summary": exploration.get("exploration_summary", ""),
            "insights": [n.id for n in insight_nodes],
            "new_curiosities": [c.id for c in new_curiosities],
            "connections": connections_made,
            "resolved": exploration.get("resolved", False),
        }

    async def explore_next(self, session_id: Optional[str] = None) -> dict:
        """
        Pick and explore the highest priority pending curiosity.
        """
        # Get pending curiosities ordered by priority
        curiosities = await self.memory.get_curiosities(
            status="pending",
            limit=1,
        )

        if not curiosities:
            return {"explored": False, "reason": "No pending curiosities"}

        return await self.explore_curiosity(curiosities[0], session_id)

    async def explore_batch(
        self,
        max_count: int = 5,
        session_id: Optional[str] = None,
    ) -> dict:
        """
        Explore multiple curiosities in one batch.
        """
        curiosities = await self.memory.get_curiosities(
            status="pending",
            limit=max_count,
        )

        results = []
        for curiosity in curiosities:
            result = await self.explore_curiosity(curiosity, session_id)
            results.append(result)

        return {
            "explored_count": len([r for r in results if r.get("explored")]),
            "total_insights": sum(len(r.get("insights", [])) for r in results),
            "total_new_curiosities": sum(len(r.get("new_curiosities", [])) for r in results),
            "results": results,
        }

    async def get_exploration_stats(self) -> dict:
        """Get statistics about exploration activity."""
        pending = await self.memory.get_curiosities(status="pending", limit=1000)
        explored = await self.memory.get_curiosities(status="explored", limit=1000)
        resolved = await self.memory.get_curiosities(status="resolved", limit=1000)

        return {
            "pending_curiosities": len(pending),
            "explored_curiosities": len(explored),
            "resolved_curiosities": len(resolved),
            "total_curiosities": len(pending) + len(explored) + len(resolved),
        }
