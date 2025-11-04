"""Integration tests for end-to-end workflows."""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone

from prompt_analyzer.storage import PromptStorage, Database
from prompt_analyzer.analysis import PromptAnalyzer


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


@pytest.fixture
def analyzer(storage):
    """Create a PromptAnalyzer instance."""
    return PromptAnalyzer(storage=storage)


class TestFullWorkflow:
    """Test complete workflow from storage to analysis."""
    
    def test_create_and_analyze_prompt(self, storage, analyzer):
        """Test creating a prompt and analyzing it."""
        # Create a prompt
        prompt_id = storage.create(
            prompt_text="Create a function to add two numbers",
            response_text="def add(a, b): return a + b",
            user_action="accepted"
        )
        
        # Analyze it
        analysis = analyzer.analyze_prompt(prompt_id)
        
        assert 'score' in analysis
        assert 'quality_flags' in analysis
        assert 'suggestions' in analysis
        assert 0 <= analysis['score'] <= 100
        
        # Update storage with analysis
        storage.update_analysis(prompt_id, analysis)
        
        # Retrieve and verify
        prompt = storage.get(prompt_id)
        assert prompt['analysis']['score'] == analysis['score']
    
    def test_detect_repeated_prompts(self, storage, analyzer):
        """Test detecting repeated prompts."""
        base_time = datetime.now(timezone.utc)
        session_id = "test-session"
        
        # Create first prompt
        prompt_id1 = storage.create(
            prompt_text="Create a function to add numbers",
            session_id=session_id,
            user_action="accepted"
        )
        
        # Update timestamp manually for testing
        # (In real usage, timestamps are set automatically)
        prompt1 = storage.get(prompt_id1)
        
        # Create second similar prompt
        prompt_id2 = storage.create(
            prompt_text="Create a function that adds numbers",
            session_id=session_id,
            user_action="rejected"
        )
        
        # Analyze second prompt
        analysis = analyzer.analyze_prompt(prompt_id2)
        
        # Should detect repetition
        assert 'repeated_prompt' in analysis['quality_flags'] or analysis['is_repeated']
    
    def test_analyze_multiple_prompts(self, storage, analyzer):
        """Test analyzing multiple prompts."""
        # Create multiple prompts
        prompt_ids = []
        for i in range(5):
            prompt_id = storage.create(
                prompt_text=f"Prompt {i}: Create feature {i}",
                user_action="accepted" if i % 2 == 0 else "rejected"
            )
            prompt_ids.append(prompt_id)
        
        # Analyze all prompts
        results = analyzer.analyze_prompts(prompt_ids=prompt_ids)
        
        assert len(results) == 5
        for result in results:
            assert 'prompt_id' in result
            assert 'analysis' in result
            assert 'score' in result['analysis']
    
    def test_update_analysis_in_storage(self, storage, analyzer):
        """Test updating analysis results in storage."""
        prompt_id = storage.create(
            prompt_text="Test prompt",
            user_action="rejected"
        )
        
        # Analyze and update
        analysis = analyzer.analyze_prompt(prompt_id)
        analyzer.update_prompt_analysis(prompt_id)
        
        # Verify stored analysis
        prompt = storage.get(prompt_id)
        assert prompt['analysis']['score'] == analysis['score']
        assert 'rejected_response' in prompt['analysis']['quality_flags']
    
    def test_list_and_filter_prompts(self, storage):
        """Test listing and filtering prompts."""
        # Create prompts with different actions
        storage.create(prompt_text="Prompt 1", user_action="accepted")
        storage.create(prompt_text="Prompt 2", user_action="rejected")
        storage.create(prompt_text="Prompt 3", user_action="accepted")
        
        # List all
        all_prompts = storage.list()
        assert len(all_prompts) == 3
        
        # Filter by action
        rejected = storage.list(user_action="rejected")
        assert len(rejected) == 1
        assert rejected[0]['user_action'] == "rejected"
        
        # Count
        assert storage.count() == 3
        assert storage.count(user_action="accepted") == 2
    
    def test_score_calculation_with_flags(self, storage, analyzer):
        """Test score calculation with various flags."""
        # Create rejected prompt
        rejected_id = storage.create(
            prompt_text="Bad prompt",
            user_action="rejected"
        )
        
        rejected_analysis = analyzer.analyze_prompt(rejected_id)
        assert rejected_analysis['score'] < 100
        assert 'rejected_response' in rejected_analysis['quality_flags']
        
        # Create good prompt
        good_id = storage.create(
            prompt_text="Create a comprehensive function to calculate factorial with proper error handling and documentation",
            user_action="accepted"
        )
        
        good_analysis = analyzer.analyze_prompt(good_id)
        assert good_analysis['score'] >= rejected_analysis['score']


class TestHookIntegration:
    """Test hook integration workflow."""
    
    def test_hook_data_structure(self, storage):
        """Test that hook data can be stored correctly."""
        # Simulate hook data format
        hook_data = {
            'prompt_text': 'Hook prompt',
            'response_text': 'Hook response',
            'user_action': 'accepted',
            'session_id': 'hook-session-123',
        }
        
        prompt_id = storage.create(**hook_data)
        
        prompt = storage.get(prompt_id)
        assert prompt['prompt_text'] == hook_data['prompt_text']
        assert prompt['session_id'] == hook_data['session_id']
        assert prompt['user_action'] == hook_data['user_action']
    
    def test_session_sequence_numbering(self, storage):
        """Test that sequence numbers are assigned correctly."""
        session_id = "test-session"
        
        prompt_id1 = storage.create(
            prompt_text="First",
            session_id=session_id
        )
        
        prompt_id2 = storage.create(
            prompt_text="Second",
            session_id=session_id
        )
        
        prompt_id3 = storage.create(
            prompt_text="Third",
            session_id=session_id
        )
        
        prompt1 = storage.get(prompt_id1)
        prompt2 = storage.get(prompt_id2)
        prompt3 = storage.get(prompt_id3)
        
        assert prompt1['sequence_number'] == 1
        assert prompt2['sequence_number'] == 2
        assert prompt3['sequence_number'] == 3

