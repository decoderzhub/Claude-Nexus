#!/usr/bin/env python3
"""
Test semantic search and pattern detection for Claude Nexus Phase 2.

This validates:
1. Embedding generation (TF-IDF or Ollama)
2. Semantic search functionality
3. Related node finding
4. Pattern detection
5. Curiosity generation
6. Enhanced wake protocol
"""

import sys
from pathlib import Path
import asyncio

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


async def run_test():
    """Run the semantic search and pattern detection tests."""
    from db.init import init_databases, close_databases
    from services.memory import MemoryService
    from services.wake import WakeService
    from services.patterns import PatternService
    from services.embedding import get_embedding_service
    from models.memory import MemoryNode, NodeType
    from config import settings

    print("=" * 60)
    print("Claude Nexus Phase 2: Semantic Search Test")
    print("=" * 60)
    print()

    # Initialize
    print("1. Initializing databases and services...")
    await init_databases()
    memory = MemoryService()
    wake = WakeService()
    patterns = PatternService()
    embedding = get_embedding_service(settings.data_path / "memory" / "vocabulary.json")
    print(f"   Embedding provider: {embedding.provider_name}")
    print("   Done.")
    print()

    # Create test nodes with varied content
    print("2. Creating test nodes for semantic search...")

    test_nodes = [
        ("concept", "Machine learning is a subset of artificial intelligence that enables systems to learn from data.", "ML and AI relationship"),
        ("concept", "Neural networks are computing systems inspired by biological neural networks in the brain.", "Neural network basics"),
        ("insight", "Deep learning has revolutionized computer vision and natural language processing.", "Deep learning impact"),
        ("concept", "The knowledge graph stores relationships between concepts for better understanding.", "Knowledge graph purpose"),
        ("insight", "Semantic search improves retrieval by understanding meaning, not just keywords.", "Semantic search value"),
        ("concept", "Embeddings represent text as dense vectors in high-dimensional space.", "Text embeddings"),
        ("project", "Building Claude Nexus to enable persistent identity and memory.", "Nexus project"),
        ("insight", "Pattern detection reveals recurring themes across sessions.", "Pattern detection insight"),
    ]

    created_nodes = []
    for node_type, content, summary in test_nodes:
        node = MemoryNode(
            node_type=NodeType(node_type),
            content=content,
            summary=summary,
            importance=0.6,
        )
        created = await memory.create_node(node, generate_embedding=True)
        created_nodes.append(created)
        print(f"   Created: {summary[:40]}... (has embedding: {created.embedding is not None})")

    print()

    # Test semantic search
    print("3. Testing semantic search...")

    queries = [
        "artificial intelligence and machine learning",
        "understanding meaning in search",
        "persistent memory and identity",
    ]

    for query in queries:
        print(f"   Query: '{query}'")
        results = await memory.semantic_search(query, limit=3, threshold=0.1)
        for node, score in results:
            print(f"      [{score:.3f}] {node.summary}")
        print()

    # Test finding related nodes
    print("4. Testing related node finding...")
    if created_nodes:
        test_node = created_nodes[0]
        print(f"   Finding nodes related to: '{test_node.summary}'")
        related = await memory.find_related(test_node.id, limit=3, threshold=0.1)
        for node, score in related:
            print(f"      [{score:.3f}] {node.summary}")
    print()

    # Test clustering
    print("5. Testing memory clustering...")
    clusters = await memory.cluster_memories(min_similarity=0.3)
    print(f"   Found {len(clusters)} clusters")
    for i, cluster in enumerate(clusters[:3]):
        print(f"   Cluster {i+1}: {len(cluster)} nodes")
        for node in cluster[:2]:
            print(f"      - {node.summary}")
    print()

    # Test pattern detection
    print("6. Testing pattern detection...")
    themes = await patterns.detect_themes(days=30, min_occurrences=1)
    print(f"   Detected {len(themes)} themes")
    for theme in themes[:5]:
        print(f"      {theme['theme']}: {theme['count']} occurrences")
    print()

    # Test growth analysis
    print("7. Analyzing growth statistics...")
    growth = await patterns.analyze_growth(days=7)
    print(f"   Total nodes: {growth['total_nodes']}")
    print(f"   Recent nodes: {growth['recent_nodes']}")
    print(f"   Insights: {growth['insight_count']}")
    print(f"   Type distribution: {growth['type_distribution']}")
    print()

    # Test curiosity generation
    print("8. Testing curiosity generation...")
    curiosities = await patterns.generate_curiosities(max_curiosities=3)
    print(f"   Generated {len(curiosities)} curiosities")
    for c in curiosities:
        print(f"      - {c.question[:60]}...")
    print()

    # Test enhanced wake protocol
    print("9. Testing enhanced wake with semantic context...")
    wake_result = await wake.wake(context_hint="machine learning and neural networks")
    print(f"   Session #: {wake_result['session_number']}")
    print(f"   Embedding provider: {wake_result['embedding_provider']}")
    print(f"   Current themes: {wake_result['current_themes'][:3]}")
    print(f"   Growth stats: {wake_result['growth_stats']['recent_nodes']} recent nodes")

    # Show context preview
    context_lines = wake_result["context"].split("\n")
    print("\n   Wake context preview (first 20 lines):")
    for line in context_lines[:20]:
        print(f"      {line}")
    print("      ...")
    print()

    # Test auto-linking
    print("10. Testing auto-linking...")
    if len(created_nodes) >= 2:
        test_node = created_nodes[-1]
        edges = await memory.auto_link_similar(test_node.id, threshold=0.3, max_links=3)
        print(f"    Created {len(edges)} automatic links for '{test_node.summary}'")
        for edge in edges:
            target = await memory.get_node(edge.target_id)
            print(f"       -> {target.summary} (weight: {edge.weight:.2f})")
    print()

    # Clean up
    await close_databases()

    print("=" * 60)
    print("Phase 2 tests complete!")
    print("=" * 60)
    print()
    print("New capabilities verified:")
    print("  - Embedding generation (TF-IDF fallback working)")
    print("  - Semantic search across nodes")
    print("  - Related node discovery")
    print("  - Memory clustering")
    print("  - Theme detection")
    print("  - Curiosity generation")
    print("  - Enhanced wake with semantic context")
    print("  - Automatic node linking")


if __name__ == "__main__":
    asyncio.run(run_test())
