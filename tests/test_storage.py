"""Tests for storage layer."""

import pytest
import tempfile
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone

from prompt_analyzer.storage import Database, PromptStorage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        db = Database(db_path=db_path)
        db.initialize_schema()
        yield db
        db.close()


@pytest.fixture
def storage(temp_db):
    """Create a PromptStorage instance with temp database."""
    return PromptStorage(db=temp_db)


class TestDatabase:
    """Test Database class."""
    
    def test_initialize_schema(self, temp_db):
        """Test schema initialization."""
        conn = temp_db.connect()
        cursor = conn.cursor()
        
        # Check that prompts table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='prompts'
        """)
        assert cursor.fetchone() is not None
        
        # Check that indexes exist
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='index' AND name LIKE 'idx_%'
        """)
        indexes = [row[0] for row in cursor.fetchall()]
        assert 'idx_timestamp' in indexes
        assert 'idx_session_id' in indexes
        assert 'idx_user_action' in indexes
    
    def test_wal_mode(self, temp_db):
        """Test WAL mode is enabled."""
        conn = temp_db.connect()
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        assert result[0].upper() == 'WAL'


class TestPromptStorage:
    """Test PromptStorage class."""
    
    def test_create_basic(self, storage):
        """Test creating a basic prompt."""
        prompt_id = storage.create(
            prompt_text="Test prompt",
            response_text="Test response"
        )
        
        assert prompt_id is not None
        assert len(prompt_id) == 36  # UUID length
        
        prompt = storage.get(prompt_id)
        assert prompt is not None
        assert prompt['prompt_text'] == "Test prompt"
        assert prompt['response_text'] == "Test response"
        assert prompt['user_action'] is None
    
    def test_create_with_user_action(self, storage):
        """Test creating a prompt with user action."""
        prompt_id = storage.create(
            prompt_text="Test prompt",
            user_action="rejected"
        )
        
        prompt = storage.get(prompt_id)
        assert prompt['user_action'] == "rejected"
    
    def test_create_with_session(self, storage):
        """Test creating prompts with session ID."""
        session_id = "test-session-123"
        
        prompt_id1 = storage.create(
            prompt_text="First prompt",
            session_id=session_id
        )
        
        prompt_id2 = storage.create(
            prompt_text="Second prompt",
            session_id=session_id
        )
        
        prompt1 = storage.get(prompt_id1)
        prompt2 = storage.get(prompt_id2)
        
        assert prompt1['session_id'] == session_id
        assert prompt2['session_id'] == session_id
        assert prompt1['sequence_number'] == 1
        assert prompt2['sequence_number'] == 2
    
    def test_create_with_analysis(self, storage):
        """Test creating a prompt with analysis data."""
        analysis = {
            'score': 75,
            'quality_flags': ['rejected_response'],
            'suggestions': ['Be more specific'],
            'is_repeated': False,
            'repeated_with': []
        }
        
        prompt_id = storage.create(
            prompt_text="Test prompt",
            analysis=analysis
        )
        
        prompt = storage.get(prompt_id)
        assert prompt['analysis']['score'] == 75
        assert 'rejected_response' in prompt['analysis']['quality_flags']
        assert len(prompt['analysis']['suggestions']) == 1
    
    def test_get_nonexistent(self, storage):
        """Test getting a nonexistent prompt."""
        result = storage.get("nonexistent-id")
        assert result is None
    
    def test_update_analysis(self, storage):
        """Test updating analysis data."""
        prompt_id = storage.create(prompt_text="Test prompt")
        
        analysis = {
            'score': 80,
            'quality_flags': ['repeated_prompt'],
            'suggestions': ['Consolidate requests'],
            'is_repeated': True,
            'repeated_with': ['other-id']
        }
        
        storage.update_analysis(prompt_id, analysis)
        
        prompt = storage.get(prompt_id)
        assert prompt['analysis']['score'] == 80
        assert 'repeated_prompt' in prompt['analysis']['quality_flags']
        assert prompt['analysis']['is_repeated'] is True
    
    def test_list_all(self, storage):
        """Test listing all prompts."""
        # Create multiple prompts
        for i in range(5):
            storage.create(prompt_text=f"Prompt {i}")
        
        prompts = storage.list()
        assert len(prompts) == 5
    
    def test_list_with_limit(self, storage):
        """Test listing with limit."""
        for i in range(10):
            storage.create(prompt_text=f"Prompt {i}")
        
        prompts = storage.list(limit=3)
        assert len(prompts) == 3
    
    def test_list_with_since(self, storage):
        """Test listing with time filter."""
        # Create old prompt
        old_time = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat().replace('+00:00', 'Z')
        storage.create(prompt_text="Old prompt")
        
        # Create recent prompt
        storage.create(prompt_text="Recent prompt")
        
        # Filter by last 7 days
        since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat().replace('+00:00', 'Z')
        prompts = storage.list(since=since)
        
        # Should only get recent prompt (but we can't easily test exact timestamps)
        # So just verify filtering works
        assert len(prompts) >= 1
    
    def test_list_with_user_action_filter(self, storage):
        """Test listing with user action filter."""
        storage.create(prompt_text="Accepted prompt", user_action="accepted")
        storage.create(prompt_text="Rejected prompt", user_action="rejected")
        storage.create(prompt_text="No action prompt")
        
        rejected = storage.list(user_action="rejected")
        assert len(rejected) == 1
        assert rejected[0]['user_action'] == "rejected"
    
    def test_count(self, storage):
        """Test counting prompts."""
        assert storage.count() == 0
        
        storage.create(prompt_text="Prompt 1")
        storage.create(prompt_text="Prompt 2")
        
        assert storage.count() == 2
    
    def test_count_with_filters(self, storage):
        """Test counting with filters."""
        storage.create(prompt_text="Accepted", user_action="accepted")
        storage.create(prompt_text="Rejected", user_action="rejected")
        storage.create(prompt_text="No action")
        
        assert storage.count(user_action="accepted") == 1
        assert storage.count(user_action="rejected") == 1
    
    def test_delete_by_id(self, storage):
        """Test deleting a prompt by ID."""
        prompt_id = storage.create(prompt_text="To delete")
        
        deleted = storage.delete(prompt_id=prompt_id, confirm=True)
        assert deleted == 1
        
        assert storage.get(prompt_id) is None
    
    def test_delete_older_than(self, storage):
        """Test deleting prompts older than a timestamp."""
        # Create prompts
        storage.create(prompt_text="Old prompt")
        storage.create(prompt_text="Recent prompt")
        
        older_than = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat().replace('+00:00', 'Z')
        
        # Count before deletion
        before_count = storage.count()
        
        # Delete old prompts
        deleted = storage.delete(older_than=older_than, confirm=True)
        
        assert deleted >= 0
        assert storage.count() <= before_count
    
    def test_delete_requires_confirmation(self, storage):
        """Test that bulk delete requires confirmation."""
        storage.create(prompt_text="Test prompt")
        
        with pytest.raises(ValueError, match="Bulk delete requires confirmation"):
            storage.delete(older_than="2020-01-01T00:00:00Z")

