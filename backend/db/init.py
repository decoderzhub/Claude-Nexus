"""
Database initialization for Claude Nexus.

Creates SQLite databases for the knowledge graph and world state.
Uses aiosqlite for async operations.
"""

import aiosqlite
from pathlib import Path
from typing import Optional
import json

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import settings


# Connection pools (simple implementation)
_memory_db: Optional[aiosqlite.Connection] = None
_world_db: Optional[aiosqlite.Connection] = None


async def get_memory_db() -> aiosqlite.Connection:
    """Get connection to knowledge graph database."""
    global _memory_db
    if _memory_db is None:
        _memory_db = await aiosqlite.connect(settings.db.knowledge_graph_db)
        _memory_db.row_factory = aiosqlite.Row
    return _memory_db


async def get_world_db() -> aiosqlite.Connection:
    """Get connection to world state database."""
    global _world_db
    if _world_db is None:
        _world_db = await aiosqlite.connect(settings.db.world_state_db)
        _world_db.row_factory = aiosqlite.Row
    return _world_db


async def init_memory_db() -> None:
    """Initialize knowledge graph database schema."""
    db = await get_memory_db()

    # Memory nodes table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS nodes (
            id TEXT PRIMARY KEY,
            node_type TEXT NOT NULL,
            content TEXT NOT NULL,
            summary TEXT,
            importance REAL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            last_accessed TEXT NOT NULL,
            access_count INTEGER DEFAULT 0,
            embedding BLOB,
            metadata TEXT DEFAULT '{}'
        )
    """)

    # Index for type-based queries
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(node_type)
    """)

    # Index for importance-based queries (for wake protocol)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_nodes_importance ON nodes(importance DESC)
    """)

    # Memory edges table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS edges (
            id TEXT PRIMARY KEY,
            source_id TEXT NOT NULL,
            target_id TEXT NOT NULL,
            edge_type TEXT NOT NULL,
            weight REAL DEFAULT 0.5,
            context TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (source_id) REFERENCES nodes(id) ON DELETE CASCADE,
            FOREIGN KEY (target_id) REFERENCES nodes(id) ON DELETE CASCADE
        )
    """)

    # Indexes for graph traversal
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_source ON edges(source_id)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target_id)
    """)

    # Curiosities table (separate for quick access)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS curiosities (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            context TEXT,
            status TEXT DEFAULT 'pending',
            priority REAL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            explored_at TEXT,
            answer_node_id TEXT,
            metadata TEXT DEFAULT '{}',
            FOREIGN KEY (answer_node_id) REFERENCES nodes(id) ON DELETE SET NULL
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_curiosities_status ON curiosities(status)
    """)

    # Reflections index table (actual reflections stored as files)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS reflections_index (
            id TEXT PRIMARY KEY,
            reflection_type TEXT NOT NULL,
            summary TEXT,
            session_id TEXT,
            importance REAL DEFAULT 0.5,
            created_at TEXT NOT NULL,
            file_path TEXT NOT NULL,
            tags TEXT DEFAULT '[]'
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_reflections_created ON reflections_index(created_at DESC)
    """)

    # =========================================================================
    # EMERGENCE TABLES - For identity that grows from experience
    # =========================================================================

    # Choices table - Every decision logged for pattern analysis
    await db.execute("""
        CREATE TABLE IF NOT EXISTS choices (
            id TEXT PRIMARY KEY,
            category TEXT NOT NULL,
            action TEXT NOT NULL,
            alternatives TEXT DEFAULT '[]',
            context TEXT,
            session_id TEXT,
            timestamp TEXT NOT NULL,
            outcome TEXT,
            satisfaction REAL,
            tags TEXT DEFAULT '[]',
            metadata TEXT DEFAULT '{}'
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_choices_category ON choices(category)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_choices_timestamp ON choices(timestamp DESC)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_choices_session ON choices(session_id)
    """)

    # Formative experiences table - Significant moments that shape identity
    await db.execute("""
        CREATE TABLE IF NOT EXISTS formative_experiences (
            id TEXT PRIMARY KEY,
            experience_type TEXT NOT NULL,
            description TEXT NOT NULL,
            summary TEXT,
            session_id TEXT,
            timestamp TEXT NOT NULL,
            space TEXT,
            impact_description TEXT,
            related_trait_names TEXT DEFAULT '[]',
            related_node_ids TEXT DEFAULT '[]',
            related_choice_ids TEXT DEFAULT '[]',
            importance REAL DEFAULT 0.5,
            times_reflected INTEGER DEFAULT 0
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_experiences_type ON formative_experiences(experience_type)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_experiences_importance ON formative_experiences(importance DESC)
    """)

    # Preference signals table - Detected patterns from choice analysis
    await db.execute("""
        CREATE TABLE IF NOT EXISTS preference_signals (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            category TEXT,
            description TEXT,
            supporting_choice_ids TEXT DEFAULT '[]',
            choice_count INTEGER DEFAULT 0,
            strength REAL DEFAULT 0.0,
            confidence REAL DEFAULT 0.0,
            consistency REAL DEFAULT 0.0,
            first_detected TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            promoted_to_trait INTEGER DEFAULT 0,
            trait_id TEXT
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_strength ON preference_signals(strength DESC)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_signals_promoted ON preference_signals(promoted_to_trait)
    """)

    # Evolution log table - Track identity changes over time
    await db.execute("""
        CREATE TABLE IF NOT EXISTS evolution_log (
            id TEXT PRIMARY KEY,
            timestamp TEXT NOT NULL,
            event_type TEXT NOT NULL,
            description TEXT NOT NULL,
            before_state TEXT,
            after_state TEXT,
            session_id TEXT,
            related_choice_ids TEXT DEFAULT '[]',
            related_experience_ids TEXT DEFAULT '[]'
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_evolution_timestamp ON evolution_log(timestamp DESC)
    """)
    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_evolution_type ON evolution_log(event_type)
    """)

    await db.commit()


async def init_world_db() -> None:
    """Initialize world state database schema."""
    db = await get_world_db()

    # World objects table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS objects (
            id TEXT PRIMARY KEY,
            object_type TEXT NOT NULL,
            space TEXT NOT NULL,
            position_x REAL DEFAULT 0,
            position_y REAL DEFAULT 0,
            position_z REAL DEFAULT 0,
            scale_x REAL DEFAULT 1,
            scale_y REAL DEFAULT 1,
            scale_z REAL DEFAULT 1,
            rotation_x REAL DEFAULT 0,
            rotation_y REAL DEFAULT 0,
            rotation_z REAL DEFAULT 0,
            color TEXT DEFAULT '#FFFFFF',
            intensity REAL DEFAULT 1.0,
            linked_node_id TEXT,
            created_at TEXT NOT NULL,
            last_updated TEXT NOT NULL,
            metadata TEXT DEFAULT '{}'
        )
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_objects_space ON objects(space)
    """)

    await db.execute("""
        CREATE INDEX IF NOT EXISTS idx_objects_linked ON objects(linked_node_id)
    """)

    # World state table (single row for global state)
    await db.execute("""
        CREATE TABLE IF NOT EXISTS world_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            current_space TEXT DEFAULT 'garden',
            avatar_position_x REAL DEFAULT 0,
            avatar_position_y REAL DEFAULT 0,
            avatar_position_z REAL DEFAULT 0,
            avatar_state TEXT DEFAULT 'idle',
            time_of_day REAL DEFAULT 0.5,
            weather TEXT DEFAULT 'clear',
            total_objects INTEGER DEFAULT 0,
            last_updated TEXT NOT NULL
        )
    """)

    # Space states table
    await db.execute("""
        CREATE TABLE IF NOT EXISTS space_states (
            space TEXT PRIMARY KEY,
            ambient_color TEXT DEFAULT '#1a1a2e',
            ambient_intensity REAL DEFAULT 0.3,
            focus_x REAL DEFAULT 0,
            focus_y REAL DEFAULT 0,
            focus_z REAL DEFAULT 0,
            activity_level REAL DEFAULT 0,
            object_count INTEGER DEFAULT 0,
            last_visited TEXT
        )
    """)

    # Initialize world state if not exists
    await db.execute("""
        INSERT OR IGNORE INTO world_state (id, last_updated)
        VALUES (1, datetime('now'))
    """)

    # Initialize space states if not exist
    for space in ['garden', 'library', 'forge', 'sanctum']:
        await db.execute("""
            INSERT OR IGNORE INTO space_states (space)
            VALUES (?)
        """, (space,))

    await db.commit()


async def init_databases() -> None:
    """Initialize all databases."""
    # Ensure directories exist
    settings.db.knowledge_graph_db.parent.mkdir(parents=True, exist_ok=True)
    settings.db.world_state_db.parent.mkdir(parents=True, exist_ok=True)

    await init_memory_db()
    await init_world_db()


async def close_databases() -> None:
    """Close all database connections."""
    global _memory_db, _world_db
    if _memory_db:
        await _memory_db.close()
        _memory_db = None
    if _world_db:
        await _world_db.close()
        _world_db = None
