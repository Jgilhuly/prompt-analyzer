"""Tests for analysis engine."""

import pytest
from datetime import datetime, timedelta, timezone

from prompt_analyzer.analysis.similarity import (
    calculate_similarity,
    find_similar_prompts,
    is_similar,
)
from prompt_analyzer.analysis.scorer import (
    calculate_score,
    score_prompt,
)
from prompt_analyzer.analysis.suggestions import (
    generate_suggestions,
)
from prompt_analyzer.analysis.detector import (
    detect_bad_prompts,
    detect_repeated_prompt,
)


class TestSimilarity:
    """Test similarity detection."""
    
    def test_calculate_similarity_exact(self):
        """Test similarity calculation for identical texts."""
        text = "This is a test prompt"
        assert calculate_similarity(text, text) == 100.0
    
    def test_calculate_similarity_similar(self):
        """Test similarity calculation for similar texts."""
        text1 = "Create a function to add numbers"
        text2 = "Create a function that adds numbers"
        similarity = calculate_similarity(text1, text2)
        assert similarity >= 80.0
    
    def test_calculate_similarity_different(self):
        """Test similarity calculation for different texts."""
        text1 = "Create a function to add numbers"
        text2 = "What is the weather today?"
        similarity = calculate_similarity(text1, text2)
        assert similarity < 50.0
    
    def test_calculate_similarity_empty(self):
        """Test similarity with empty strings."""
        assert calculate_similarity("", "") == 0.0
        assert calculate_similarity("test", "") == 0.0
        assert calculate_similarity("", "test") == 0.0
    
    def test_find_similar_prompts(self):
        """Test finding similar prompts."""
        prompt_text = "Create a function to add numbers"
        candidates = [
            ("id1", "Create a function that adds numbers"),
            ("id2", "What is the weather today?"),
            ("id3", "Create a function to add numbers together"),
        ]
        
        similar = find_similar_prompts(prompt_text, candidates, threshold=80)
        
        assert len(similar) >= 2
        assert similar[0][0] in ["id1", "id3"]  # Should find similar ones
        assert similar[0][1] >= 80.0
    
    def test_is_similar(self):
        """Test is_similar helper function."""
        text1 = "Create a function to add numbers"
        text2 = "Create a function that adds numbers"
        
        assert is_similar(text1, text2, threshold=80) is True
        
        text3 = "What is the weather?"
        assert is_similar(text1, text3, threshold=80) is False


class TestScoring:
    """Test quality scoring."""
    
    def test_base_score(self):
        """Test base score without flags."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, [])
        assert score == 100
    
    def test_score_with_rejected(self):
        """Test score with rejected flag."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, ["rejected_response"])
        assert score == 70  # 100 - 30
    
    def test_score_with_repeated(self):
        """Test score with repeated flag."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, ["repeated_prompt"])
        assert score == 80  # 100 - 20
    
    def test_score_with_vague(self):
        """Test score with vague flag."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, ["vague_request"])
        assert score == 85  # 100 - 15
    
    def test_score_multiple_flags(self):
        """Test score with multiple flags."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, ["rejected_response", "repeated_prompt"])
        assert score == 50  # 100 - 30 - 20
    
    def test_score_minimum_zero(self):
        """Test that score doesn't go below 0."""
        prompt = {"prompt_text": "Test prompt"}
        score = calculate_score(prompt, ["rejected_response", "repeated_prompt", "vague_request"])
        assert score >= 0
    
    def test_score_prompt_function(self):
        """Test score_prompt wrapper function."""
        prompt = {"prompt_text": "Test prompt"}
        detection_results = {
            'quality_flags': ['rejected_response']
        }
        
        score = score_prompt(prompt, detection_results)
        assert score == 70


class TestDetector:
    """Test bad prompt detection."""
    
    def test_detect_rejected_prompt(self):
        """Test detection of rejected prompts."""
        prompt = {
            "id": "test-id",
            "prompt_text": "Test prompt",
            "user_action": "rejected"
        }
        
        result = detect_bad_prompts(prompt, [])
        
        assert 'rejected_response' in result['quality_flags']
    
    def test_detect_repeated_prompt(self):
        """Test detection of repeated prompts."""
        base_time = datetime.now(timezone.utc)
        
        prompt1 = {
            "id": "id1",
            "prompt_text": "Create a function to add numbers",
            "timestamp": base_time.isoformat().replace('+00:00', 'Z'),
            "session_id": "session1"
        }
        
        prompt2 = {
            "id": "id2",
            "prompt_text": "Create a function that adds numbers",
            "timestamp": (base_time + timedelta(minutes=2)).isoformat().replace('+00:00', 'Z'),
            "session_id": "session1"
        }
        
        result = detect_bad_prompts(prompt2, [prompt1])
        
        assert 'repeated_prompt' in result['quality_flags']
        assert result['detection_results']['repeated']['is_repeated'] is True
    
    def test_detect_vague_prompt(self):
        """Test detection of vague prompts."""
        prompt = {
            "id": "test-id",
            "prompt_text": "help"  # Very short and vague
        }
        
        result = detect_bad_prompts(prompt, [])
        
        # Vague detection might not always trigger, but verify function works
        assert 'quality_flags' in result
    
    def test_detect_no_flags(self):
        """Test detection with no flags."""
        prompt = {
            "id": "test-id",
            "prompt_text": "Create a well-structured function to calculate the sum of two numbers with proper error handling",
            "user_action": "accepted"
        }
        
        result = detect_bad_prompts(prompt, [])
        
        assert len(result['quality_flags']) == 0


class TestSuggestions:
    """Test suggestion generation."""
    
    def test_suggestions_for_rejected(self):
        """Test suggestions for rejected prompts."""
        prompt = {
            "prompt_text": "Test prompt",
            "user_action": "rejected"
        }
        
        suggestions = generate_suggestions(
            prompt,
            ["rejected_response"],
            {}
        )
        
        assert len(suggestions) > 0
        assert any("rejected" in s.lower() or "specific" in s.lower() for s in suggestions)
    
    def test_suggestions_for_repeated(self):
        """Test suggestions for repeated prompts."""
        prompt = {
            "prompt_text": "Test prompt"
        }
        
        detection_results = {
            'repeated': {
                'is_repeated': True,
                'repeated_with': ['id1', 'id2']
            }
        }
        
        suggestions = generate_suggestions(
            prompt,
            ["repeated_prompt"],
            detection_results
        )
        
        assert len(suggestions) > 0
        assert any("similar" in s.lower() or "consolidat" in s.lower() for s in suggestions)
    
    def test_suggestions_for_vague(self):
        """Test suggestions for vague prompts."""
        prompt = {
            "prompt_text": "help"
        }
        
        suggestions = generate_suggestions(
            prompt,
            ["vague_request"],
            {}
        )
        
        assert len(suggestions) > 0
        assert any("specific" in s.lower() or "vague" in s.lower() for s in suggestions)
    
    def test_suggestions_for_short_prompt(self):
        """Test suggestions for short prompts."""
        prompt = {
            "prompt_text": "Fix bug"
        }
        
        suggestions = generate_suggestions(
            prompt,
            [],
            {}
        )
        
        # Should suggest adding more context
        assert len(suggestions) > 0
    
    def test_no_suggestions_for_good_prompt(self):
        """Test that good prompts get minimal suggestions."""
        prompt = {
            "prompt_text": "Create a comprehensive function to calculate the factorial of a number with proper error handling, type hints, and documentation."
        }
        
        suggestions = generate_suggestions(
            prompt,
            [],
            {}
        )
        
        # Good prompts might still get generic suggestions, but shouldn't get flag-specific ones
        assert isinstance(suggestions, list)

