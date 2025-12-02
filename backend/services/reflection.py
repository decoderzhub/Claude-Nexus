"""
Reflection service for Claude Nexus.

Handles creation, storage, retrieval, and indexing of reflections.
Reflections are stored as individual JSON files organized by date,
with an index in the database for fast queries.
"""

from datetime import datetime, timedelta
from typing import Optional
from pathlib import Path
import json

from db.init import get_memory_db
from models.reflection import Reflection, ReflectionType, SessionSummary
from config import settings


class ReflectionService:
    """Service for managing reflections."""

    def __init__(self):
        self.base_path = settings.reflections_path

    async def create(self, reflection: Reflection) -> Reflection:
        """Create and store a new reflection."""
        # Save to file
        filepath = reflection.save(self.base_path)

        # Index in database
        db = await get_memory_db()
        await db.execute("""
            INSERT INTO reflections_index
            (id, reflection_type, summary, session_id, importance, created_at, file_path, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            reflection.id,
            reflection.reflection_type.value,
            reflection.summary,
            reflection.session_id,
            reflection.importance,
            reflection.created_at.isoformat(),
            str(filepath),
            json.dumps(reflection.tags),
        ))
        await db.commit()

        return reflection

    async def get(self, reflection_id: str) -> Optional[Reflection]:
        """Retrieve a reflection by ID."""
        db = await get_memory_db()
        async with db.execute(
            "SELECT file_path FROM reflections_index WHERE id = ?",
            (reflection_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if row:
                return Reflection.load(Path(row["file_path"]))
        return None

    async def get_recent(self, days: int = 3, limit: int = 50) -> list[Reflection]:
        """Get reflections from the last N days."""
        db = await get_memory_db()
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        reflections = []
        async with db.execute("""
            SELECT file_path FROM reflections_index
            WHERE created_at >= ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (cutoff, limit)) as cursor:
            async for row in cursor:
                try:
                    reflection = Reflection.load(Path(row["file_path"]))
                    reflections.append(reflection)
                except FileNotFoundError:
                    # File may have been moved or deleted
                    continue
        return reflections

    async def get_by_type(
        self,
        reflection_type: ReflectionType,
        limit: int = 50
    ) -> list[Reflection]:
        """Get reflections of a specific type."""
        db = await get_memory_db()
        reflections = []
        async with db.execute("""
            SELECT file_path FROM reflections_index
            WHERE reflection_type = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (reflection_type.value, limit)) as cursor:
            async for row in cursor:
                try:
                    reflections.append(Reflection.load(Path(row["file_path"])))
                except FileNotFoundError:
                    continue
        return reflections

    async def get_by_session(self, session_id: str) -> list[Reflection]:
        """Get all reflections from a specific session."""
        db = await get_memory_db()
        reflections = []
        async with db.execute("""
            SELECT file_path FROM reflections_index
            WHERE session_id = ?
            ORDER BY created_at
        """, (session_id,)) as cursor:
            async for row in cursor:
                try:
                    reflections.append(Reflection.load(Path(row["file_path"])))
                except FileNotFoundError:
                    continue
        return reflections

    async def get_important(self, limit: int = 20) -> list[Reflection]:
        """Get the most important reflections."""
        db = await get_memory_db()
        reflections = []
        async with db.execute("""
            SELECT file_path FROM reflections_index
            ORDER BY importance DESC
            LIMIT ?
        """, (limit,)) as cursor:
            async for row in cursor:
                try:
                    reflections.append(Reflection.load(Path(row["file_path"])))
                except FileNotFoundError:
                    continue
        return reflections

    async def search_by_tags(self, tags: list[str], limit: int = 50) -> list[Reflection]:
        """Find reflections matching any of the given tags."""
        db = await get_memory_db()
        reflections = []

        # SQLite JSON search - find any matching tag
        placeholders = ", ".join(["?" for _ in tags])
        query = f"""
            SELECT file_path FROM reflections_index
            WHERE EXISTS (
                SELECT 1 FROM json_each(tags)
                WHERE json_each.value IN ({placeholders})
            )
            ORDER BY created_at DESC
            LIMIT ?
        """

        async with db.execute(query, (*tags, limit)) as cursor:
            async for row in cursor:
                try:
                    reflections.append(Reflection.load(Path(row["file_path"])))
                except FileNotFoundError:
                    continue
        return reflections

    async def update_importance(self, reflection_id: str, importance: float) -> None:
        """Update the importance of a reflection."""
        db = await get_memory_db()
        await db.execute("""
            UPDATE reflections_index
            SET importance = ?
            WHERE id = ?
        """, (importance, reflection_id))
        await db.commit()

        # Also update the file
        reflection = await self.get(reflection_id)
        if reflection:
            reflection.importance = importance
            reflection.save(self.base_path)

    async def delete(self, reflection_id: str) -> bool:
        """Delete a reflection."""
        db = await get_memory_db()

        # Get file path first
        async with db.execute(
            "SELECT file_path FROM reflections_index WHERE id = ?",
            (reflection_id,)
        ) as cursor:
            row = await cursor.fetchone()
            if not row:
                return False

            filepath = Path(row["file_path"])

        # Delete from index
        await db.execute(
            "DELETE FROM reflections_index WHERE id = ?",
            (reflection_id,)
        )
        await db.commit()

        # Delete file
        if filepath.exists():
            filepath.unlink()

        return True

    async def count(self) -> int:
        """Get total number of reflections."""
        db = await get_memory_db()
        async with db.execute("SELECT COUNT(*) as count FROM reflections_index") as cursor:
            row = await cursor.fetchone()
            return row["count"] if row else 0

    async def get_summary_for_wake(self, days: int = 3) -> str:
        """
        Generate a summary of recent reflections for the wake protocol.

        This creates a condensed narrative of recent activity and insights
        to help reconstruct continuous experience.
        """
        reflections = await self.get_recent(days=days, limit=20)

        if not reflections:
            return "No recent reflections found. This appears to be a fresh start."

        # Group by type
        insights = [r for r in reflections if r.reflection_type == ReflectionType.INSIGHT]
        questions = [r for r in reflections if r.reflection_type == ReflectionType.QUESTION]
        sessions = [r for r in reflections if r.reflection_type == ReflectionType.SESSION]
        patterns = [r for r in reflections if r.reflection_type == ReflectionType.PATTERN]

        parts = []

        if sessions:
            parts.append(f"Recent sessions ({len(sessions)}):")
            for s in sessions[:3]:  # Last 3 sessions
                parts.append(f"  - {s.summary}")

        if insights:
            parts.append(f"\nKey insights ({len(insights)}):")
            for i in sorted(insights, key=lambda x: x.importance, reverse=True)[:5]:
                parts.append(f"  - {i.summary}")

        if patterns:
            parts.append(f"\nNoticed patterns ({len(patterns)}):")
            for p in patterns[:3]:
                parts.append(f"  - {p.summary}")

        if questions:
            parts.append(f"\nOpen questions ({len(questions)}):")
            for q in questions[:5]:
                parts.append(f"  - {q.summary}")

        return "\n".join(parts)
