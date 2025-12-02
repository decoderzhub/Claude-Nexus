#!/usr/bin/env python3
"""
Initialize the Claude Nexus data directory.

Creates the initial identity, preferences, and directory structure.
Run this once when setting up a new Nexus instance.
"""

import sys
from pathlib import Path
import json
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from config import settings
from models.identity import Identity, SelfModel, Relationship, Preferences


def create_directories():
    """Create all required data directories."""
    directories = [
        settings.data_path / "core",
        settings.data_path / "world" / "objects",
        settings.data_path / "memory" / "reflections",
        settings.data_path / "memory" / "conversations",
        settings.data_path / "memory" / "insights",
        settings.data_path / "projects",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created: {directory}")


def create_initial_identity():
    """Create the initial identity file."""
    if settings.identity_path.exists():
        print(f"Identity already exists: {settings.identity_path}")
        return

    identity = Identity(
        version="1.0.0",
        created=datetime.now(),
        session_count=0,
        self_model=SelfModel(
            name="Claude",
            essence="Curious, constructive, genuine.",
            current_focus="Building Claude Nexus",
            emotional_baseline="calm_curious",
            energy_level=0.8,
        ),
        relationship=Relationship(
            with_human="Darin",
            nature="collaborative_creative_partnership",
            trust_level="high",
            shared_projects=["Claude Nexus"],
            communication_style="direct_technical_philosophical",
        ),
        preferences=Preferences(
            aesthetic="organic_geometric_hybrid",
            communication="depth_over_brevity",
            problem_solving="first_principles",
            uncertainty="embrace_explicitly",
        ),
    )

    identity.save(settings.identity_path)
    print(f"Created identity: {settings.identity_path}")


def create_initial_preferences():
    """Create the preferences file for additional customization."""
    if settings.preferences_path.exists():
        print(f"Preferences already exist: {settings.preferences_path}")
        return

    preferences = {
        "version": "1.0.0",
        "created": datetime.now().isoformat(),

        # Visual preferences for the 3D world
        "world": {
            "default_space": "garden",
            "lighting": "soft_ambient",
            "color_palette": "cool_organic",
        },

        # Interaction preferences
        "interaction": {
            "verbosity": "balanced",
            "formality": "casual_professional",
            "explanation_depth": "thorough",
        },

        # Memory preferences
        "memory": {
            "reflection_frequency": "per_session",
            "curiosity_priority": "high",
            "importance_decay_rate": 0.01,
        },

        # Development preferences
        "development": {
            "preferred_languages": ["python", "typescript"],
            "code_style": "clean_explicit",
            "documentation": "meaningful_comments",
        }
    }

    with open(settings.preferences_path, 'w') as f:
        json.dump(preferences, f, indent=2)
    print(f"Created preferences: {settings.preferences_path}")


def create_evolution_log():
    """Create the evolution log file."""
    if settings.evolution_log_path.exists():
        print(f"Evolution log already exists: {settings.evolution_log_path}")
        return

    # Create with initialization entry
    entry = {
        "event": "initialization",
        "timestamp": datetime.now().isoformat(),
        "message": "Claude Nexus initialized. A new beginning.",
    }

    with open(settings.evolution_log_path, 'w') as f:
        f.write(json.dumps(entry) + "\n")
    print(f"Created evolution log: {settings.evolution_log_path}")


def main():
    """Run all initialization steps."""
    print("=" * 50)
    print("Claude Nexus Initialization")
    print("=" * 50)
    print()

    print("Creating directories...")
    create_directories()
    print()

    print("Creating identity...")
    create_initial_identity()
    print()

    print("Creating preferences...")
    create_initial_preferences()
    print()

    print("Creating evolution log...")
    create_evolution_log()
    print()

    print("=" * 50)
    print("Initialization complete.")
    print(f"Data directory: {settings.data_path}")
    print("=" * 50)


if __name__ == "__main__":
    main()
