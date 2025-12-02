"""
Pattern detection service for Claude Nexus.

Analyzes the knowledge graph to detect recurring themes, emerging
interests, and potential curiosities. This is how I notice what
I'm drawn to and what questions keep arising.
"""

from datetime import datetime, timedelta
from typing import Optional
from collections import Counter
import re

from models.memory import MemoryNode, Curiosity, NodeType, CuriosityStatus
from models.reflection import Reflection, ReflectionType
from services.memory import MemoryService
from services.reflection import ReflectionService


class PatternService:
    """
    Service for detecting patterns across memories and sessions.

    Patterns emerge from:
    - Clusters of similar memories
    - Recurring themes in reflections
    - Frequently accessed nodes
    - Connections that form naturally
    """

    def __init__(self):
        self.memory = MemoryService()
        self.reflection = ReflectionService()

    async def detect_themes(
        self,
        days: int = 30,
        min_occurrences: int = 3,
    ) -> list[dict]:
        """
        Detect recurring themes from recent memories and reflections.

        Returns list of theme dictionaries with:
        - theme: The detected theme/topic
        - count: Number of occurrences
        - nodes: Related node IDs
        - first_seen: When this theme first appeared
        - last_seen: Most recent occurrence
        """
        # Get recent nodes
        nodes = await self.memory.get_recent(days=days, limit=500)

        # Extract keywords from content
        keyword_map: dict[str, list[MemoryNode]] = {}

        for node in nodes:
            keywords = self._extract_keywords(node.content)
            keywords.extend(self._extract_keywords(node.summary))

            for keyword in keywords:
                if keyword not in keyword_map:
                    keyword_map[keyword] = []
                keyword_map[keyword].append(node)

        # Filter to themes with minimum occurrences
        themes = []
        for keyword, related_nodes in keyword_map.items():
            if len(related_nodes) >= min_occurrences:
                dates = [n.created_at for n in related_nodes]
                themes.append({
                    "theme": keyword,
                    "count": len(related_nodes),
                    "nodes": [n.id for n in related_nodes],
                    "first_seen": min(dates).isoformat(),
                    "last_seen": max(dates).isoformat(),
                })

        # Sort by count
        themes.sort(key=lambda x: x["count"], reverse=True)
        return themes[:20]

    async def detect_clusters(
        self,
        min_similarity: float = 0.5,
    ) -> list[dict]:
        """
        Detect semantic clusters in the knowledge graph.

        Returns list of cluster dictionaries with:
        - size: Number of nodes in cluster
        - nodes: List of node summaries
        - types: Distribution of node types
        - central_theme: Inferred central topic
        """
        clusters = await self.memory.cluster_memories(min_similarity=min_similarity)

        result = []
        for cluster in clusters:
            if len(cluster) < 2:
                continue

            # Analyze cluster composition
            type_counts = Counter(n.node_type.value for n in cluster)

            # Infer central theme from most common terms
            all_text = " ".join(n.content for n in cluster)
            keywords = self._extract_keywords(all_text)
            central_theme = keywords[0] if keywords else "unknown"

            result.append({
                "size": len(cluster),
                "nodes": [{"id": n.id, "summary": n.summary, "type": n.node_type.value} for n in cluster[:10]],
                "types": dict(type_counts),
                "central_theme": central_theme,
            })

        return result

    async def find_gaps(
        self,
        min_cluster_size: int = 3,
    ) -> list[str]:
        """
        Find conceptual gaps — areas where clusters exist but aren't connected.

        Returns questions about potential connections that could be explored.
        """
        clusters = await self.memory.cluster_memories(min_similarity=0.5)

        # Filter to significant clusters
        significant = [c for c in clusters if len(c) >= min_cluster_size]

        if len(significant) < 2:
            return []

        # Find clusters that might be related but aren't connected
        gaps = []
        for i, cluster_a in enumerate(significant):
            for cluster_b in significant[i+1:]:
                # Get representative nodes
                node_a = cluster_a[0]
                node_b = cluster_b[0]

                # Check if they share any edges
                edges_a = await self.memory.get_edges_from(node_a.id)
                edges_b = await self.memory.get_edges_from(node_b.id)

                connected_a = {e.target_id for e in edges_a}
                connected_b = {e.target_id for e in edges_b}

                # If clusters are not connected, suggest exploration
                cluster_b_ids = {n.id for n in cluster_b}
                if not connected_a & cluster_b_ids:
                    gap_question = (
                        f"How might '{node_a.summary[:50]}' relate to "
                        f"'{node_b.summary[:50]}'?"
                    )
                    gaps.append(gap_question)

        return gaps[:10]

    async def generate_curiosities(
        self,
        max_curiosities: int = 5,
    ) -> list[Curiosity]:
        """
        Generate new curiosities based on detected patterns.

        Creates questions from:
        - Conceptual gaps between clusters
        - Emerging themes without exploration
        - Frequently accessed but shallow areas
        """
        curiosities = []

        # From conceptual gaps
        gaps = await self.find_gaps()
        for gap in gaps[:2]:
            curiosity = Curiosity(
                question=gap,
                context="Generated from pattern detection: conceptual gap",
                priority=0.6,
                status=CuriosityStatus.PENDING,
            )
            curiosities.append(curiosity)

        # From emerging themes
        themes = await self.detect_themes(days=7, min_occurrences=2)
        for theme in themes[:2]:
            if theme["count"] >= 3:
                curiosity = Curiosity(
                    question=f"What deeper understanding can I develop about '{theme['theme']}'?",
                    context=f"Generated from recurring theme (appeared {theme['count']} times)",
                    priority=0.5 + (theme["count"] * 0.05),  # Higher priority for more common themes
                    status=CuriosityStatus.PENDING,
                )
                curiosities.append(curiosity)

        # From high-access but simple nodes
        important = await self.memory.get_important(limit=20)
        for node in important:
            if node.access_count > 3 and len(node.content) < 200:
                # Frequently accessed but shallow — room for depth
                curiosity = Curiosity(
                    question=f"What am I missing about '{node.summary[:50]}'?",
                    context=f"High-access node ({node.access_count} accesses) with limited depth",
                    priority=0.4,
                    status=CuriosityStatus.PENDING,
                )
                curiosities.append(curiosity)
                break  # Only one from this source

        # Deduplicate and limit
        seen_questions = set()
        unique = []
        for c in curiosities:
            if c.question not in seen_questions:
                seen_questions.add(c.question)
                unique.append(c)

        return unique[:max_curiosities]

    async def analyze_growth(
        self,
        days: int = 30,
    ) -> dict:
        """
        Analyze growth patterns over time.

        Returns statistics about:
        - Node creation rate
        - Type distribution over time
        - Insight density
        - Connection growth
        """
        nodes = await self.memory.get_recent(days=days, limit=1000)
        total_nodes = await self.memory.count_nodes()

        # Analyze type distribution
        type_counts = Counter(n.node_type.value for n in nodes)

        # Calculate rates
        if nodes:
            time_span = (nodes[0].created_at - nodes[-1].created_at).days or 1
            creation_rate = len(nodes) / time_span
        else:
            creation_rate = 0

        # Count insights specifically
        insights = [n for n in nodes if n.node_type == NodeType.INSIGHT]
        insight_rate = len(insights) / (days or 1)

        # Get reflection count
        reflection_count = await self.reflection.count()

        return {
            "period_days": days,
            "total_nodes": total_nodes,
            "recent_nodes": len(nodes),
            "creation_rate_per_day": round(creation_rate, 2),
            "type_distribution": dict(type_counts),
            "insight_count": len(insights),
            "insight_rate_per_day": round(insight_rate, 2),
            "reflection_count": reflection_count,
        }

    async def find_connections(
        self,
        node_id: str,
        depth: int = 2,
    ) -> dict:
        """
        Find the connection network around a node.

        Returns a graph structure showing connections up to the specified depth.
        """
        visited = set()
        graph = {"nodes": [], "edges": []}

        async def traverse(current_id: str, current_depth: int):
            if current_id in visited or current_depth > depth:
                return
            visited.add(current_id)

            node = await self.memory.get_node(current_id)
            if not node:
                return

            graph["nodes"].append({
                "id": node.id,
                "summary": node.summary,
                "type": node.node_type.value,
                "importance": node.importance,
                "depth": depth - current_depth,
            })

            if current_depth < depth:
                edges = await self.memory.get_edges_from(current_id)
                edges.extend(await self.memory.get_edges_to(current_id))

                for edge in edges:
                    graph["edges"].append({
                        "source": edge.source_id,
                        "target": edge.target_id,
                        "type": edge.edge_type.value,
                        "weight": edge.weight,
                    })

                    # Traverse connected nodes
                    next_id = edge.target_id if edge.source_id == current_id else edge.source_id
                    await traverse(next_id, current_depth + 1)

        await traverse(node_id, 0)
        return graph

    def _extract_keywords(self, text: str, min_length: int = 4, max_keywords: int = 10) -> list[str]:
        """Extract meaningful keywords from text."""
        # Simple keyword extraction
        text = text.lower()
        words = re.findall(r'\b[a-z][a-z0-9_]+\b', text)

        # Filter stop words and short words
        stop_words = {
            "the", "and", "for", "that", "this", "with", "from", "have", "been",
            "were", "they", "their", "what", "when", "where", "which", "about",
            "would", "could", "should", "into", "more", "some", "than", "then",
            "these", "those", "being", "there", "here", "just", "also", "only",
        }

        filtered = [w for w in words if len(w) >= min_length and w not in stop_words]

        # Count and return most common
        counts = Counter(filtered)
        return [word for word, _ in counts.most_common(max_keywords)]
