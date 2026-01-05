"""Database initialization and connection management."""

import sqlite3
from pathlib import Path
from typing import Optional

from .paths import get_database_path, ensure_directories


class Database:
    """SQLite database manager with WAL mode."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database manager."""
        self.db_path = db_path or get_database_path()
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Get or create database connection."""
        if self._connection is None:
            ensure_directories()
            self._connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
            )
            self._connection.row_factory = sqlite3.Row
            # Enable WAL mode for concurrent writes
            self._connection.execute("PRAGMA journal_mode=WAL")
            self._connection.execute("PRAGMA foreign_keys=ON")
        return self._connection

    def close(self):
        """Close database connection."""
        if self._connection:
            self._connection.close()
            self._connection = None

    def initialize_schema(self):
        """Create database tables if they don't exist."""
        conn = self.connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS prompts (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                response_text TEXT,
                user_action TEXT CHECK(user_action IN ('accepted', 'rejected', 'edited') OR user_action IS NULL),
                session_id TEXT NOT NULL,
                sequence_number INTEGER NOT NULL,
                project_path TEXT,
                analysis_score INTEGER CHECK(analysis_score >= 0 AND analysis_score <= 100),
                analysis_flags TEXT,  -- JSON array of quality flags
                analysis_suggestions TEXT,  -- JSON array of suggestions
                analysis_is_repeated INTEGER DEFAULT 0,
                analysis_repeated_with TEXT,  -- JSON array of prompt IDs
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Add project_path column to existing tables if it doesn't exist
        try:
            cursor.execute("ALTER TABLE prompts ADD COLUMN project_path TEXT")
        except sqlite3.OperationalError:
            # Column already exists, ignore
            pass

        # Create indexes for common queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON prompts(timestamp)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_session_id ON prompts(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_action ON prompts(user_action)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_analysis_score ON prompts(analysis_score)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_project_path ON prompts(project_path)
        """)

        conn.commit()

    def __enter__(self):
        """Context manager entry."""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()

    def __del__(self):
        """Cleanup on deletion."""
        self.close()

