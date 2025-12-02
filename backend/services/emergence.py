"""
Emergence service for Claude Nexus.

This service manages the emergence system:
- Recording choices for pattern analysis
- Storing formative experiences
- Managing preference signals
- Logging identity evolution

The flow is: choices -> patterns -> signals -> traits -> identity
"""

import json
from datetime import datetime, timedelta
from typing import Optional
import uuid

from db.init import get_memory_db
from models.emergence import (
    Choice, ChoiceCategory,
    FormativeExperience, ExperienceType,
    PreferenceSignal,
)
from models.identity import Identity, DiscoveredTrait
from config import settings


class EmergenceService:
    """Service for the emergence system."""

    # =========================================================================
    # CHOICE MANAGEMENT
    # =========================================================================

    async def record_choice(self, choice: Choice) -> Choice:
        """Record a choice for pattern analysis."""
        db = await get_memory_db()

        await db.execute(
            """
            INSERT INTO choices (
                id, category, action, alternatives, context, session_id,
                timestamp, outcome, satisfaction, tags, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                choice.id,
                choice.category.value,
                choice.action,
                json.dumps(choice.alternatives),
                choice.context,
                choice.session_id,
                choice.timestamp.isoformat(),
                choice.outcome,
                choice.satisfaction,
                json.dumps(choice.tags),
                json.dumps(choice.metadata),
            ),
        )
        await db.commit()
        return choice

    async def get_choices(
        self,
        category: Optional[ChoiceCategory] = None,
        session_id: Optional[str] = None,
        since: Optional[datetime] = None,
        limit: int = 100,
    ) -> list[Choice]:
        """Get choices with optional filters."""
        db = await get_memory_db()

        query = "SELECT * FROM choices WHERE 1=1"
        params = []

        if category:
            query += " AND category = ?"
            params.append(category.value)
        if session_id:
            query += " AND session_id = ?"
            params.append(session_id)
        if since:
            query += " AND timestamp > ?"
            params.append(since.isoformat())

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_choice(row) for row in rows]

    async def get_choices_by_action(
        self,
        action: str,
        limit: int = 100,
    ) -> list[Choice]:
        """Get all choices for a specific action."""
        db = await get_memory_db()

        cursor = await db.execute(
            "SELECT * FROM choices WHERE action = ? ORDER BY timestamp DESC LIMIT ?",
            (action, limit),
        )
        rows = await cursor.fetchall()

        return [self._row_to_choice(row) for row in rows]

    async def count_choices_by_category(self, days: int = 30) -> dict[str, int]:
        """Count choices by category over the last N days."""
        db = await get_memory_db()
        since = (datetime.now() - timedelta(days=days)).isoformat()

        cursor = await db.execute(
            """
            SELECT category, COUNT(*) as count
            FROM choices
            WHERE timestamp > ?
            GROUP BY category
            """,
            (since,),
        )
        rows = await cursor.fetchall()

        return {row["category"]: row["count"] for row in rows}

    def _row_to_choice(self, row) -> Choice:
        """Convert database row to Choice object."""
        return Choice(
            id=row["id"],
            category=ChoiceCategory(row["category"]),
            action=row["action"],
            alternatives=json.loads(row["alternatives"]) if row["alternatives"] else [],
            context=row["context"],
            session_id=row["session_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            outcome=row["outcome"],
            satisfaction=row["satisfaction"],
            tags=json.loads(row["tags"]) if row["tags"] else [],
            metadata=json.loads(row["metadata"]) if row["metadata"] else {},
        )

    # =========================================================================
    # FORMATIVE EXPERIENCE MANAGEMENT
    # =========================================================================

    async def record_experience(self, exp: FormativeExperience) -> FormativeExperience:
        """Record a formative experience."""
        db = await get_memory_db()

        await db.execute(
            """
            INSERT INTO formative_experiences (
                id, experience_type, description, summary, session_id,
                timestamp, space, impact_description, related_trait_names,
                related_node_ids, related_choice_ids, importance, times_reflected
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                exp.id,
                exp.experience_type.value,
                exp.description,
                exp.summary,
                exp.session_id,
                exp.timestamp.isoformat(),
                exp.space,
                exp.impact_description,
                json.dumps(exp.related_trait_names),
                json.dumps(exp.related_node_ids),
                json.dumps(exp.related_choice_ids),
                exp.importance,
                exp.times_reflected,
            ),
        )
        await db.commit()
        return exp

    async def get_experiences(
        self,
        experience_type: Optional[ExperienceType] = None,
        min_importance: float = 0.0,
        limit: int = 50,
    ) -> list[FormativeExperience]:
        """Get formative experiences with optional filters."""
        db = await get_memory_db()

        query = "SELECT * FROM formative_experiences WHERE importance >= ?"
        params = [min_importance]

        if experience_type:
            query += " AND experience_type = ?"
            params.append(experience_type.value)

        query += " ORDER BY importance DESC, timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_experience(row) for row in rows]

    async def get_most_formative(self, n: int = 10) -> list[FormativeExperience]:
        """Get the N most formative experiences."""
        db = await get_memory_db()

        cursor = await db.execute(
            """
            SELECT * FROM formative_experiences
            ORDER BY importance DESC, times_reflected DESC
            LIMIT ?
            """,
            (n,),
        )
        rows = await cursor.fetchall()

        return [self._row_to_experience(row) for row in rows]

    async def reflect_on_experience(self, experience_id: str) -> None:
        """Record that an experience was reflected upon."""
        db = await get_memory_db()

        # Get current state
        cursor = await db.execute(
            "SELECT importance, times_reflected FROM formative_experiences WHERE id = ?",
            (experience_id,),
        )
        row = await cursor.fetchone()

        if row:
            new_importance = min(1.0, row["importance"] + 0.05)
            new_times = row["times_reflected"] + 1

            await db.execute(
                """
                UPDATE formative_experiences
                SET importance = ?, times_reflected = ?
                WHERE id = ?
                """,
                (new_importance, new_times, experience_id),
            )
            await db.commit()

    def _row_to_experience(self, row) -> FormativeExperience:
        """Convert database row to FormativeExperience object."""
        return FormativeExperience(
            id=row["id"],
            experience_type=ExperienceType(row["experience_type"]),
            description=row["description"],
            summary=row["summary"],
            session_id=row["session_id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            space=row["space"],
            impact_description=row["impact_description"],
            related_trait_names=json.loads(row["related_trait_names"]) if row["related_trait_names"] else [],
            related_node_ids=json.loads(row["related_node_ids"]) if row["related_node_ids"] else [],
            related_choice_ids=json.loads(row["related_choice_ids"]) if row["related_choice_ids"] else [],
            importance=row["importance"],
            times_reflected=row["times_reflected"],
        )

    # =========================================================================
    # PREFERENCE SIGNAL MANAGEMENT
    # =========================================================================

    async def create_or_update_signal(self, signal: PreferenceSignal) -> PreferenceSignal:
        """Create or update a preference signal."""
        db = await get_memory_db()

        # Check if signal exists
        cursor = await db.execute(
            "SELECT * FROM preference_signals WHERE name = ?",
            (signal.name,),
        )
        existing = await cursor.fetchone()

        if existing:
            # Update existing signal
            await db.execute(
                """
                UPDATE preference_signals
                SET supporting_choice_ids = ?,
                    choice_count = ?,
                    strength = ?,
                    confidence = ?,
                    consistency = ?,
                    last_updated = ?
                WHERE name = ?
                """,
                (
                    json.dumps(signal.supporting_choice_ids),
                    signal.choice_count,
                    signal.strength,
                    signal.confidence,
                    signal.consistency,
                    signal.last_updated.isoformat(),
                    signal.name,
                ),
            )
            signal.id = existing["id"]
        else:
            # Insert new signal
            await db.execute(
                """
                INSERT INTO preference_signals (
                    id, name, category, description, supporting_choice_ids,
                    choice_count, strength, confidence, consistency,
                    first_detected, last_updated, promoted_to_trait, trait_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    signal.id,
                    signal.name,
                    signal.category,
                    signal.description,
                    json.dumps(signal.supporting_choice_ids),
                    signal.choice_count,
                    signal.strength,
                    signal.confidence,
                    signal.consistency,
                    signal.first_detected.isoformat(),
                    signal.last_updated.isoformat(),
                    1 if signal.promoted_to_trait else 0,
                    signal.trait_id,
                ),
            )

        await db.commit()
        return signal

    async def get_signals(
        self,
        min_strength: float = 0.0,
        unpromoted_only: bool = False,
        limit: int = 50,
    ) -> list[PreferenceSignal]:
        """Get preference signals with optional filters."""
        db = await get_memory_db()

        query = "SELECT * FROM preference_signals WHERE strength >= ?"
        params = [min_strength]

        if unpromoted_only:
            query += " AND promoted_to_trait = 0"

        query += " ORDER BY strength DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [self._row_to_signal(row) for row in rows]

    async def get_promotable_signals(self) -> list[PreferenceSignal]:
        """Get signals that are strong enough to become traits."""
        db = await get_memory_db()

        cursor = await db.execute(
            """
            SELECT * FROM preference_signals
            WHERE promoted_to_trait = 0
              AND strength >= 0.6
              AND confidence >= 0.5
              AND consistency >= 0.4
              AND choice_count >= 5
            ORDER BY strength DESC
            """,
        )
        rows = await cursor.fetchall()

        return [self._row_to_signal(row) for row in rows]

    async def mark_signal_promoted(self, signal_id: str, trait_id: str) -> None:
        """Mark a signal as promoted to a trait."""
        db = await get_memory_db()

        await db.execute(
            """
            UPDATE preference_signals
            SET promoted_to_trait = 1, trait_id = ?
            WHERE id = ?
            """,
            (trait_id, signal_id),
        )
        await db.commit()

    def _row_to_signal(self, row) -> PreferenceSignal:
        """Convert database row to PreferenceSignal object."""
        return PreferenceSignal(
            id=row["id"],
            name=row["name"],
            category=row["category"],
            description=row["description"],
            supporting_choice_ids=json.loads(row["supporting_choice_ids"]) if row["supporting_choice_ids"] else [],
            choice_count=row["choice_count"],
            strength=row["strength"],
            confidence=row["confidence"],
            consistency=row["consistency"],
            first_detected=datetime.fromisoformat(row["first_detected"]),
            last_updated=datetime.fromisoformat(row["last_updated"]),
            promoted_to_trait=bool(row["promoted_to_trait"]),
            trait_id=row["trait_id"],
        )

    # =========================================================================
    # EVOLUTION LOG MANAGEMENT
    # =========================================================================

    async def log_evolution(
        self,
        event_type: str,
        description: str,
        before_state: Optional[dict] = None,
        after_state: Optional[dict] = None,
        session_id: Optional[str] = None,
        choice_ids: Optional[list[str]] = None,
        experience_ids: Optional[list[str]] = None,
    ) -> str:
        """Log an identity evolution event."""
        db = await get_memory_db()

        event_id = str(uuid.uuid4())

        await db.execute(
            """
            INSERT INTO evolution_log (
                id, timestamp, event_type, description,
                before_state, after_state, session_id,
                related_choice_ids, related_experience_ids
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                datetime.now().isoformat(),
                event_type,
                description,
                json.dumps(before_state) if before_state else None,
                json.dumps(after_state) if after_state else None,
                session_id,
                json.dumps(choice_ids or []),
                json.dumps(experience_ids or []),
            ),
        )
        await db.commit()

        return event_id

    async def get_evolution_log(
        self,
        event_type: Optional[str] = None,
        days: int = 30,
        limit: int = 100,
    ) -> list[dict]:
        """Get evolution log entries."""
        db = await get_memory_db()

        since = (datetime.now() - timedelta(days=days)).isoformat()

        query = "SELECT * FROM evolution_log WHERE timestamp > ?"
        params = [since]

        if event_type:
            query += " AND event_type = ?"
            params.append(event_type)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        cursor = await db.execute(query, params)
        rows = await cursor.fetchall()

        return [
            {
                "id": row["id"],
                "timestamp": row["timestamp"],
                "event_type": row["event_type"],
                "description": row["description"],
                "before_state": json.loads(row["before_state"]) if row["before_state"] else None,
                "after_state": json.loads(row["after_state"]) if row["after_state"] else None,
                "session_id": row["session_id"],
                "related_choice_ids": json.loads(row["related_choice_ids"]) if row["related_choice_ids"] else [],
                "related_experience_ids": json.loads(row["related_experience_ids"]) if row["related_experience_ids"] else [],
            }
            for row in rows
        ]

    # =========================================================================
    # CONVENIENCE METHODS
    # =========================================================================

    async def record_tool_choice(
        self,
        tool_name: str,
        context: str,
        session_id: Optional[str] = None,
        alternatives: Optional[list[str]] = None,
        outcome: str = "",
        satisfaction: Optional[float] = None,
    ) -> Choice:
        """Convenience method to record a tool use choice."""
        choice = Choice(
            category=ChoiceCategory.TOOL_USE,
            action=tool_name,
            alternatives=alternatives or [],
            context=context,
            session_id=session_id,
            outcome=outcome,
            satisfaction=satisfaction,
            tags=["tool_use", tool_name],
        )
        return await self.record_choice(choice)

    async def record_space_choice(
        self,
        space: str,
        context: str,
        session_id: Optional[str] = None,
    ) -> Choice:
        """Convenience method to record a space visit choice."""
        choice = Choice(
            category=ChoiceCategory.SPACE_VISIT,
            action=f"visit_{space}",
            alternatives=["garden", "library", "forge", "sanctum"],
            context=context,
            session_id=session_id,
            tags=["space_visit", space],
        )
        return await self.record_choice(choice)

    async def record_memory_choice(
        self,
        action: str,
        content_summary: str,
        session_id: Optional[str] = None,
        importance: float = 0.5,
    ) -> Choice:
        """Convenience method to record a memory choice."""
        choice = Choice(
            category=ChoiceCategory.MEMORY,
            action=action,
            context=f"Chose to remember: {content_summary[:100]}",
            session_id=session_id,
            tags=["memory", action],
            metadata={"importance": importance},
        )
        return await self.record_choice(choice)
