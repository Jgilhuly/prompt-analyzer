"""Storage path utilities."""

import os
from pathlib import Path


def get_storage_dir() -> Path:
    """Get the storage directory path (~/.prompt-analyzer)."""
    return Path.home() / ".prompt-analyzer"


def get_data_dir() -> Path:
    """Get the data directory path (~/.prompt-analyzer/data)."""
    return get_storage_dir() / "data"


def get_database_path() -> Path:
    """Get the database file path (~/.prompt-analyzer/data/prompts.db)."""
    return get_data_dir() / "prompts.db"


def get_config_path() -> Path:
    """Get the config file path (~/.prompt-analyzer/config.json)."""
    return get_storage_dir() / "config.json"


def ensure_directories():
    """Ensure storage directories exist."""
    get_data_dir().mkdir(parents=True, exist_ok=True)

