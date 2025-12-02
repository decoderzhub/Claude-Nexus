"""
Configuration for Claude Nexus backend.

All paths are relative to allow mounting data directory to different locations.
The DATA_PATH environment variable can override the default data location.
"""

import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional

# Load .env file if present
from dotenv import load_dotenv
load_dotenv()


# Base paths - relative to project root
PROJECT_ROOT = Path(__file__).parent.parent
DEFAULT_DATA_PATH = PROJECT_ROOT / "data"

# Allow override via environment variable for NAS mounting
DATA_PATH = Path(os.getenv("NEXUS_DATA_PATH", str(DEFAULT_DATA_PATH)))


@dataclass
class DatabaseSettings:
    """Database configuration."""
    knowledge_graph_db: Path
    world_state_db: Path

    def __post_init__(self):
        # Ensure parent directories exist
        self.knowledge_graph_db.parent.mkdir(parents=True, exist_ok=True)
        self.world_state_db.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class Settings:
    """Application settings."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # CORS
    cors_origins: list[str] = None

    # Paths
    data_path: Path = DATA_PATH

    # Database
    db: DatabaseSettings = None

    # Wake/Sleep
    recent_reflection_days: int = 3
    important_memory_limit: int = 20

    # Embedding (for future use with sentence-transformers or Ollama)
    embedding_model: str = "all-MiniLM-L6-v2"
    embedding_dimension: int = 384

    # Anthropic API
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096

    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["http://localhost:3000"]

        if self.db is None:
            self.db = DatabaseSettings(
                knowledge_graph_db=self.data_path / "memory" / "knowledge_graph.db",
                world_state_db=self.data_path / "world" / "world_state.db"
            )

        # Load Anthropic API key from environment
        if self.anthropic_api_key is None:
            self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        # Allow model override from environment
        env_model = os.getenv("ANTHROPIC_MODEL")
        if env_model:
            self.anthropic_model = env_model

    @property
    def identity_path(self) -> Path:
        return self.data_path / "core" / "identity.json"

    @property
    def preferences_path(self) -> Path:
        return self.data_path / "core" / "preferences.json"

    @property
    def evolution_log_path(self) -> Path:
        return self.data_path / "core" / "evolution.log"

    @property
    def reflections_path(self) -> Path:
        return self.data_path / "memory" / "reflections"

    @property
    def conversations_path(self) -> Path:
        return self.data_path / "memory" / "conversations"

    @property
    def insights_path(self) -> Path:
        return self.data_path / "memory" / "insights"

    @property
    def projects_path(self) -> Path:
        return self.data_path / "projects"


# Global settings instance
settings = Settings()
