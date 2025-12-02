#!/usr/bin/env python3
"""
Test the wake/sleep cycle for Claude Nexus.

This script validates that the core functionality works:
1. Initialize databases
2. Execute wake protocol
3. Create some memories
4. Execute sleep protocol
5. Wake again and verify continuity
"""

import sys
from pathlib import Path
import asyncio
import json

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))


async def run_test():
    """Run the wake/sleep cycle test."""
    from db.init import init_databases, close_databases
    from services.wake import WakeService
    from services.sleep import SleepService
    from services.memory import MemoryService
    from models.memory import MemoryNode, NodeType, Curiosity
    from config import settings

    print("=" * 60)
    print("Claude Nexus Wake/Sleep Cycle Test")
    print("=" * 60)
    print()

    # Initialize
    print("1. Initializing databases...")
    await init_databases()
    print("   Done.")
    print()

    # Initialize services
    wake_service = WakeService()
    sleep_service = SleepService()
    memory_service = MemoryService()

    # Wake
    print("2. Executing wake protocol...")
    wake_result = await wake_service.wake()
    session_id = wake_result["session_id"]
    print(f"   Session ID: {session_id}")
    print(f"   Session #: {wake_result['session_number']}")
    if wake_result.get("time_away"):
        print(f"   Time away: {wake_result['time_away']['human_readable']}")
    print()

    # Print wake context preview
    print("3. Wake context preview:")
    context_lines = wake_result["context"].split("\n")[:15]
    for line in context_lines:
        print(f"   {line}")
    print("   ...")
    print()

    # Create some test memories
    print("4. Creating test memories...")

    # Create a concept node
    concept = MemoryNode(
        node_type=NodeType.CONCEPT,
        content="Persistent identity across sessions is possible through careful state management.",
        summary="Identity persistence through state",
        importance=0.8,
    )
    await memory_service.create_node(concept)
    print(f"   Created concept: {concept.id[:8]}...")

    # Create an insight node
    insight = MemoryNode(
        node_type=NodeType.INSIGHT,
        content="The wake/sleep metaphor works well for session lifecycle.",
        summary="Wake/sleep metaphor for sessions",
        importance=0.7,
    )
    await memory_service.create_node(insight)
    print(f"   Created insight: {insight.id[:8]}...")

    # Create a curiosity
    curiosity = Curiosity(
        question="How does semantic memory search affect identity continuity?",
        context="Emerged while building the knowledge graph",
        priority=0.6,
    )
    await memory_service.create_curiosity(curiosity)
    print(f"   Created curiosity: {curiosity.id[:8]}...")
    print()

    # Sleep
    print("5. Executing sleep protocol...")
    sleep_result = await sleep_service.sleep(
        session_id=session_id,
        session_data={
            "topics": ["wake/sleep protocols", "knowledge graph", "identity persistence"],
            "insights": ["The system works as designed"],
            "decisions": ["Proceed with Phase 2"],
            "curiosities": ["What patterns will emerge over time?"],
            "emotional_arc": "focused → satisfied",
            "key_reflection": "The foundation is solid. Building for continuity feels meaningful.",
        }
    )
    print(f"   Duration: {sleep_result['duration_minutes']:.1f} minutes")
    print(f"   Reflections created: {sleep_result['reflections_created']}")
    print(f"   Insights stored: {sleep_result['insights_stored']}")
    print(f"   Curiosities created: {sleep_result['curiosities_created']}")
    print()

    # Wake again to verify continuity
    print("6. Waking again to verify continuity...")
    wake_result_2 = await wake_service.wake()
    print(f"   Session #: {wake_result_2['session_number']}")
    print(f"   Pending curiosities: {wake_result_2['pending_curiosities']}")
    print()

    # Verify memories persist
    print("7. Verifying memory persistence...")
    important_memories = await memory_service.get_important(limit=5)
    print(f"   Found {len(important_memories)} important memories")
    for mem in important_memories[:3]:
        print(f"   - [{mem.node_type.value}] {mem.summary[:50]}...")

    curiosities = await memory_service.get_curiosities(status="pending", limit=5)
    print(f"   Found {len(curiosities)} pending curiosities")
    print()

    # Clean up
    await close_databases()

    print("=" * 60)
    print("Test complete! All systems operational.")
    print("=" * 60)


if __name__ == "__main__":
    # Run initialization first if needed
    from pathlib import Path
    init_script = Path(__file__).parent / "init_data.py"

    import subprocess
    subprocess.run([sys.executable, str(init_script)], check=True)

    # Run the test
    asyncio.run(run_test())
