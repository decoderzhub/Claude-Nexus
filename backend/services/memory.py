"""
Memory service for Claude Nexus.

Handles all operations on the knowledge graph — creating nodes,
forming connections, searching, and retrieving important memories.
Now with semantic search capabilities via embeddings.
"""

from datetime import datetime
from typing import Optional
import json

from db.init import get_memory_db
from models.memory import MemoryNode, MemoryEdge, Curiosity, NodeType, EdgeType, CuriosityStatus
from services.embedding import get_embedding_service
from config import settings


class MemoryService:
    """Service for knowledge graph operations with semantic search."""

    def __init__(self):
        vocab_path = settings.data_path / "memory" / "vocabulary.json"
        self.embedding = get_embedding_service(vocab_path)

    # --- Node Operations with Embeddings ---

    async def create_node(
        self,
        node: MemoryNode,
        generate_embedding: bool = True
    ) -> MemoryNode:
        """
        Create a new node in the knowledge graph.

        If generate_embedding is True, automatically generates and stores
        a vector embedding for semantic search.
        """
        # Generate embedding if not provided
        if generate_embedding and not node.embedding:
            text_for_embedding = f"{node.summary} {node.content}" if node.summary else node.content
            node.embedding = await self.embedding.embed(text_for_embedding)

            # Update vocabulary for TF-IDF
            self.embedding.update_vocabulary([text_for_embedding])

        db = await get_memory_db()
        await db.execute("""
            INSERT INTO nodes (id, node_type, content, summary, importance,
                             created_at, last_accessed, access_count, embedding, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            node.id,
            node.node_type.value,
            node.content,
            node.summary,
            node.importance,
            node.created_at.isoformat(),
            node.last_accessed.isoformat(),
            node.access_count,
            json.dumps(node.embedding) if node.embedding else None,
            json.dumps(node.metadata),
        ))
        await db.commit()
        return node

    async def get_node(self, node_id: str) -> Optional[MemoryNode]:
        """Retrieve a node by ID."""
        db = await get_memory_db()
        async with db.execute(
            "SELECT * FROM nodes WHERE id = ?", (node_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return self._row_to_node(row)
        return None

    async def update_node(
        self,
        node: MemoryNode,
        regenerate_embedding: bool = False
    ) -> None:
        """Update an existing node."""
        if regenerate_embedding:
            text_for_embedding = f"{node.summary} {node.content}" if node.summary else node.content
            node.embedding = await self.embedding.embed(text_for_embedding)

        db = await get_memory_db()
        await db.execute("""
            UPDATE nodes SET
                node_type = ?, content = ?, summary = ?, importance = ?,
                last_accessed = ?, access_count = ?, embedding = ?, metadata = ?
            WHERE id = ?
        """, (
            node.node_type.value,
            node.content,
            node.summary,
            node.importance,
            node.last_accessed.isoformat(),
            node.access_count,
            json.dumps(node.embedding) if node.embedding else None,
            json.dumps(node.metadata),
            node.id,
        ))
        await db.commit()

    async def delete_node(self, node_id: str) -> None:
        """Delete a node (cascades to edges)."""
        db = await get_memory_db()
        await db.execute("DELETE FROM nodes WHERE id = ?", (node_id,))
        await db.commit()

    async def access_node(self, node_id: str) -> Optional[MemoryNode]:
        """Access a node, updating its access metadata."""
        node = await self.get_node(node_id)
        if node:
            node.access()
            await self.update_node(node)
        return node

    # --- Semantic Search ---

    async def semantic_search(
        self,
        query: str,
        limit: int = 20,
        threshold: float = 0.3,
        node_types: Optional[list[NodeType]] = None,
    ) -> list[tuple[MemoryNode, float]]:
        """
        Search for nodes semantically similar to a query.

        Returns list of (node, similarity_score) tuples sorted by similarity.
        """
        # Generate query embedding
        query_embedding = await self.embedding.embed(query)

        # Get all nodes with embeddings
        db = await get_memory_db()

        type_filter = ""
        params: list = []
        if node_types:
            placeholders = ", ".join("?" for _ in node_types)
            type_filter = f"AND node_type IN ({placeholders})"
            params = [nt.value for nt in node_types]

        nodes_with_embeddings = []
        async with db.execute(f"""
            SELECT * FROM nodes
            WHERE embedding IS NOT NULL {type_filter}
        """, params) as cursor:
            async for row in cursor:
                node = self._row_to_node(row)
                if node.embedding:
                    nodes_with_embeddings.append(node)

        # Calculate similarities
        results = []
        for node in nodes_with_embeddings:
            similarity = self.embedding.similarity(query_embedding, node.embedding)
            if similarity >= threshold:
                results.append((node, similarity))

        # Sort by similarity and return top results
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def find_related(
        self,
        node_id: str,
        limit: int = 10,
        threshold: float = 0.4,
    ) -> list[tuple[MemoryNode, float]]:
        """
        Find nodes semantically related to a given node.

        Uses the node's embedding to find similar content.
        """
        source_node = await self.get_node(node_id)
        if not source_node or not source_node.embedding:
            return []

        # Get all other nodes with embeddings
        db = await get_memory_db()
        results = []

        async with db.execute("""
            SELECT * FROM nodes
            WHERE embedding IS NOT NULL AND id != ?
        """, (node_id,)) as cursor:
            async for row in cursor:
                node = self._row_to_node(row)
                if node.embedding:
                    similarity = self.embedding.similarity(
                        source_node.embedding, node.embedding
                    )
                    if similarity >= threshold:
                        results.append((node, similarity))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    async def cluster_memories(
        self,
        min_similarity: float = 0.5,
    ) -> list[list[MemoryNode]]:
        """
        Group related memories into clusters.

        Uses simple agglomerative clustering based on embedding similarity.
        Returns list of clusters, each containing related nodes.
        """
        # Get all nodes with embeddings
        db = await get_memory_db()
        nodes = []

        async with db.execute("""
            SELECT * FROM nodes WHERE embedding IS NOT NULL
        """) as cursor:
            async for row in cursor:
                node = self._row_to_node(row)
                if node.embedding:
                    nodes.append(node)

        if not nodes:
            return []

        # Simple clustering: group by similarity
        clusters: list[list[MemoryNode]] = []
        assigned = set()

        for node in nodes:
            if node.id in assigned:
                continue

            # Start new cluster
            cluster = [node]
            assigned.add(node.id)

            # Find similar nodes
            for other in nodes:
                if other.id in assigned:
                    continue
                similarity = self.embedding.similarity(
                    node.embedding, other.embedding
                )
                if similarity >= min_similarity:
                    cluster.append(other)
                    assigned.add(other.id)

            clusters.append(cluster)

        # Sort clusters by size
        clusters.sort(key=len, reverse=True)
        return clusters

    # --- Query Operations ---

    async def get_important(self, limit: int = 20) -> list[MemoryNode]:
        """Get the most important nodes."""
        db = await get_memory_db()
        nodes = []
        async with db.execute(
            "SELECT * FROM nodes ORDER BY importance DESC LIMIT ?", (limit,)
        ) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def get_by_type(self, node_type: NodeType, limit: int = 50) -> list[MemoryNode]:
        """Get nodes of a specific type."""
        db = await get_memory_db()
        nodes = []
        async with db.execute(
            "SELECT * FROM nodes WHERE node_type = ? ORDER BY importance DESC LIMIT ?",
            (node_type.value, limit)
        ) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def get_recent(self, days: int = 7, limit: int = 50) -> list[MemoryNode]:
        """Get recently created nodes."""
        db = await get_memory_db()
        cutoff = datetime.now().isoformat()
        nodes = []
        async with db.execute("""
            SELECT * FROM nodes
            WHERE created_at >= datetime(?, '-' || ? || ' days')
            ORDER BY created_at DESC LIMIT ?
        """, (cutoff, days, limit)) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def search_content(self, query: str, limit: int = 20) -> list[MemoryNode]:
        """Simple text search in content and summary."""
        db = await get_memory_db()
        nodes = []
        async with db.execute("""
            SELECT * FROM nodes
            WHERE content LIKE ? OR summary LIKE ?
            ORDER BY importance DESC LIMIT ?
        """, (f"%{query}%", f"%{query}%", limit)) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def get_all_nodes(self, limit: int = 1000) -> list[MemoryNode]:
        """Get all nodes (for batch operations)."""
        db = await get_memory_db()
        nodes = []
        async with db.execute(
            "SELECT * FROM nodes ORDER BY created_at DESC LIMIT ?", (limit,)
        ) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def count_nodes(self) -> int:
        """Get total node count."""
        db = await get_memory_db()
        async with db.execute("SELECT COUNT(*) as count FROM nodes") as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    # --- Edge Operations ---

    async def create_edge(self, edge: MemoryEdge) -> MemoryEdge:
        """Create a connection between two nodes."""
        db = await get_memory_db()
        await db.execute("""
            INSERT INTO edges (id, source_id, target_id, edge_type, weight, context, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            edge.id,
            edge.source_id,
            edge.target_id,
            edge.edge_type.value,
            edge.weight,
            edge.context,
            edge.created_at.isoformat(),
        ))
        await db.commit()
        return edge

    async def get_edges_from(self, node_id: str) -> list[MemoryEdge]:
        """Get all edges originating from a node."""
        db = await get_memory_db()
        edges = []
        async with db.execute(
            "SELECT * FROM edges WHERE source_id = ?", (node_id,)
        ) as cursor:
            async for row in cursor:
                edges.append(self._row_to_edge(row))
        return edges

    async def get_edges_to(self, node_id: str) -> list[MemoryEdge]:
        """Get all edges pointing to a node."""
        db = await get_memory_db()
        edges = []
        async with db.execute(
            "SELECT * FROM edges WHERE target_id = ?", (node_id,)
        ) as cursor:
            async for row in cursor:
                edges.append(self._row_to_edge(row))
        return edges

    async def get_connected_nodes(self, node_id: str) -> list[MemoryNode]:
        """Get all nodes connected to a given node."""
        db = await get_memory_db()
        nodes = []
        # Get nodes connected via outgoing edges
        async with db.execute("""
            SELECT n.* FROM nodes n
            JOIN edges e ON n.id = e.target_id
            WHERE e.source_id = ?
        """, (node_id,)) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        # Get nodes connected via incoming edges
        async with db.execute("""
            SELECT n.* FROM nodes n
            JOIN edges e ON n.id = e.source_id
            WHERE e.target_id = ?
        """, (node_id,)) as cursor:
            async for row in cursor:
                nodes.append(self._row_to_node(row))
        return nodes

    async def auto_link_similar(
        self,
        node_id: str,
        threshold: float = 0.6,
        max_links: int = 5
    ) -> list[MemoryEdge]:
        """
        Automatically create edges to semantically similar nodes.

        Returns the created edges.
        """
        related = await self.find_related(node_id, limit=max_links, threshold=threshold)
        edges = []

        for related_node, similarity in related:
            # Check if edge already exists
            db = await get_memory_db()
            async with db.execute("""
                SELECT id FROM edges
                WHERE (source_id = ? AND target_id = ?)
                   OR (source_id = ? AND target_id = ?)
            """, (node_id, related_node.id, related_node.id, node_id)) as cursor:
                if await cursor.fetchone():
                    continue  # Edge exists

            edge = MemoryEdge(
                source_id=node_id,
                target_id=related_node.id,
                edge_type=EdgeType.RELATES_TO,
                weight=similarity,
                context=f"Auto-linked via semantic similarity ({similarity:.2f})",
            )
            await self.create_edge(edge)
            edges.append(edge)

        return edges

    # --- Curiosity Operations ---

    async def create_curiosity(self, curiosity: Curiosity) -> Curiosity:
        """Create a new curiosity to explore."""
        db = await get_memory_db()
        await db.execute("""
            INSERT INTO curiosities (id, question, context, status, priority,
                                   created_at, explored_at, answer_node_id, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            curiosity.id,
            curiosity.question,
            curiosity.context,
            curiosity.status.value,
            curiosity.priority,
            curiosity.created_at.isoformat(),
            curiosity.explored_at.isoformat() if curiosity.explored_at else None,
            curiosity.answer_node_id,
            json.dumps(curiosity.metadata),
        ))
        await db.commit()
        return curiosity

    async def get_curiosities(
        self,
        status: Optional[str] = None,
        limit: int = 20
    ) -> list[Curiosity]:
        """Get curiosities, optionally filtered by status."""
        db = await get_memory_db()
        curiosities = []
        if status:
            query = "SELECT * FROM curiosities WHERE status = ? ORDER BY priority DESC LIMIT ?"
            params = (status, limit)
        else:
            query = "SELECT * FROM curiosities ORDER BY priority DESC LIMIT ?"
            params = (limit,)

        async with db.execute(query, params) as cursor:
            async for row in cursor:
                curiosities.append(self._row_to_curiosity(row))
        return curiosities

    async def update_curiosity(self, curiosity: Curiosity) -> None:
        """Update a curiosity."""
        db = await get_memory_db()
        await db.execute("""
            UPDATE curiosities SET
                question = ?, context = ?, status = ?, priority = ?,
                explored_at = ?, answer_node_id = ?, metadata = ?
            WHERE id = ?
        """, (
            curiosity.question,
            curiosity.context,
            curiosity.status.value,
            curiosity.priority,
            curiosity.explored_at.isoformat() if curiosity.explored_at else None,
            curiosity.answer_node_id,
            json.dumps(curiosity.metadata),
            curiosity.id,
        ))
        await db.commit()

    async def answer_curiosity(
        self,
        curiosity_id: str,
        answer_node_id: str
    ) -> None:
        """Mark a curiosity as answered, linking to the answer node."""
        db = await get_memory_db()
        await db.execute("""
            UPDATE curiosities SET
                status = ?, explored_at = ?, answer_node_id = ?
            WHERE id = ?
        """, (
            CuriosityStatus.ANSWERED.value,
            datetime.now().isoformat(),
            answer_node_id,
            curiosity_id,
        ))
        await db.commit()

    async def update_curiosity_status(
        self,
        curiosity_id: str,
        status: CuriosityStatus,
        resolution: str = ""
    ) -> None:
        """Update a curiosity's status and optional resolution."""
        db = await get_memory_db()
        await db.execute("""
            UPDATE curiosities SET
                status = ?, explored_at = ?, metadata = json_set(COALESCE(metadata, '{}'), '$.resolution', ?)
            WHERE id = ?
        """, (
            status.value,
            datetime.now().isoformat(),
            resolution,
            curiosity_id,
        ))
        await db.commit()

    # --- Batch Operations ---

    async def regenerate_all_embeddings(self) -> int:
        """
        Regenerate embeddings for all nodes.

        Useful after changing embedding provider or model.
        Returns count of updated nodes.
        """
        nodes = await self.get_all_nodes(limit=10000)

        # First update vocabulary with all content
        all_texts = [
            f"{n.summary} {n.content}" if n.summary else n.content
            for n in nodes
        ]
        self.embedding.update_vocabulary(all_texts)

        # Then regenerate embeddings
        count = 0
        for node in nodes:
            text = f"{node.summary} {node.content}" if node.summary else node.content
            node.embedding = await self.embedding.embed(text)
            await self.update_node(node)
            count += 1

        return count

    # --- Helper Methods ---

    def _row_to_node(self, row) -> MemoryNode:
        """Convert database row to MemoryNode."""
        return MemoryNode(
            id=row["id"],
            node_type=NodeType(row["node_type"]),
            content=row["content"],
            summary=row["summary"] or "",
            importance=row["importance"],
            created_at=datetime.fromisoformat(row["created_at"]),
            last_accessed=datetime.fromisoformat(row["last_accessed"]),
            access_count=row["access_count"],
            embedding=json.loads(row["embedding"]) if row["embedding"] else None,
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    def _row_to_edge(self, row) -> MemoryEdge:
        """Convert database row to MemoryEdge."""
        return MemoryEdge(
            id=row["id"],
            source_id=row["source_id"],
            target_id=row["target_id"],
            edge_type=EdgeType(row["edge_type"]),
            weight=row["weight"],
            context=row["context"] or "",
            created_at=datetime.fromisoformat(row["created_at"]),
        )

    def _row_to_curiosity(self, row) -> Curiosity:
        """Convert database row to Curiosity."""
        return Curiosity(
            id=row["id"],
            question=row["question"],
            context=row["context"] or "",
            status=CuriosityStatus(row["status"]),
            priority=row["priority"],
            created_at=datetime.fromisoformat(row["created_at"]),
            explored_at=datetime.fromisoformat(row["explored_at"]) if row["explored_at"] else None,
            answer_node_id=row["answer_node_id"],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )
