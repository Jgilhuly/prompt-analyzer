"""Tests for UI formatters."""

import pytest
from datetime import datetime, timedelta

from prompt_analyzer.ui import (
    format_stats,
    format_examples,
    format_storage_info,
    format_timestamp,
    parse_time_range,
)


class TestFormatTimestamp:
    """Test timestamp formatting."""
    
    def test_format_iso_timestamp(self):
        """Test formatting ISO timestamp."""
        iso = "2024-01-15T10:30:00Z"
        formatted = format_timestamp(iso)
        assert "2024-01-15" in formatted
        assert "10:30:00" in formatted
    
    def test_format_invalid_timestamp(self):
        """Test formatting invalid timestamp."""
        invalid = "not-a-timestamp"
        formatted = format_timestamp(invalid)
        assert formatted == invalid


class TestParseTimeRange:
    """Test time range parsing."""
    
    def test_parse_days(self):
        """Test parsing days format."""
        result = parse_time_range("7d")
        assert result is not None
        assert isinstance(result, str)
        assert result.endswith("Z")
    
    def test_parse_hours(self):
        """Test parsing hours format."""
        result = parse_time_range("24h")
        assert result is not None
    
    def test_parse_weeks(self):
        """Test parsing weeks format."""
        result = parse_time_range("2w")
        assert result is not None
    
    def test_parse_months(self):
        """Test parsing months format."""
        result = parse_time_range("1m")
        assert result is not None
    
    def test_parse_invalid(self):
        """Test parsing invalid format."""
        result = parse_time_range("invalid")
        assert result is None
    
    def test_parse_empty(self):
        """Test parsing empty string."""
        result = parse_time_range("")
        assert result is None


class TestFormatStats:
    """Test statistics formatting."""
    
    def test_format_basic_stats(self):
        """Test formatting basic statistics."""
        stats = {
            'total_prompts': 10,
            'date_range': '2024-01-01 to 2024-01-07',
            'quality_breakdown': {
                'rejected': 2,
                'repeated': 1,
                'accepted': 5,
                'edited': 1,
                'no_action': 1,
            },
            'score_stats': {
                'average': 75.5,
                'median': 80,
                'min': 50,
                'max': 100,
            },
            'trends': [],
        }
        
        output = format_stats(stats)
        assert "Total Prompts: 10" in output
        assert "Rejected: 2" in output
        assert "Average: 75.5" in output
    
    def test_format_stats_with_trends(self):
        """Test formatting stats with trends."""
        stats = {
            'total_prompts': 20,
            'date_range': '2024-01-01 to 2024-01-07',
            'quality_breakdown': {
                'rejected': 5,
                'repeated': 2,
                'accepted': 10,
                'edited': 2,
                'no_action': 1,
            },
            'score_stats': {},
            'trends': ['✅ Rejection rate improved: 30.0% → 20.0%'],
        }
        
        output = format_stats(stats)
        assert "improved" in output.lower()


class TestFormatExamples:
    """Test examples formatting."""
    
    def test_format_examples_empty(self):
        """Test formatting empty examples list."""
        output = format_examples([])
        assert "No prompts found" in output
    
    def test_format_examples_with_prompt(self):
        """Test formatting examples with prompts."""
        examples = [
            {
                'id': 'test-id-1',
                'timestamp': '2024-01-15T10:30:00Z',
                'prompt_text': 'Create a function to add numbers',
                'user_action': 'accepted',
                'analysis': {
                    'score': 85,
                    'quality_flags': [],
                    'suggestions': [],
                }
            }
        ]
        
        output = format_examples(examples)
        assert 'test-id-1' in output
        assert 'Create a function' in output
        assert '85/100' in output
    
    def test_format_examples_with_analysis(self):
        """Test formatting examples with analysis."""
        examples = [
            {
                'id': 'test-id-2',
                'timestamp': '2024-01-15T10:30:00Z',
                'prompt_text': 'Fix bug',
                'user_action': 'rejected',
                'analysis': {
                    'score': 70,
                    'quality_flags': ['rejected_response'],
                    'suggestions': ['Be more specific'],
                    'is_repeated': False,
                    'repeated_with': [],
                }
            }
        ]
        
        output = format_examples(examples)
        assert '⚠️' in output or 'rejected' in output.lower()
        assert 'Be more specific' in output
    
    def test_format_examples_with_limit(self):
        """Test formatting examples with limit."""
        examples = [
            {
                'id': f'test-id-{i}',
                'timestamp': '2024-01-15T10:30:00Z',
                'prompt_text': f'Prompt {i}',
                'analysis': {'score': 80, 'quality_flags': [], 'suggestions': []}
            }
            for i in range(10)
        ]
        
        output = format_examples(examples, limit=3)
        # Should only show first 3
        assert 'test-id-0' in output
        assert 'test-id-1' in output
        assert 'test-id-2' in output


class TestFormatStorageInfo:
    """Test storage info formatting."""
    
    def test_format_storage_info(self):
        """Test formatting storage information."""
        info = {
            'database_path': '/path/to/database.db',
            'database_size': '1.5 MB',
            'total_prompts': 100,
            'oldest_prompt': '2024-01-01T00:00:00Z',
            'newest_prompt': '2024-01-15T23:59:59Z',
        }
        
        output = format_storage_info(info)
        assert '/path/to/database.db' in output
        assert '1.5 MB' in output
        assert '100' in output
    
    def test_format_storage_info_minimal(self):
        """Test formatting minimal storage info."""
        info = {
            'database_path': '/path/to/database.db',
            'database_size': 'N/A',
            'total_prompts': 0,
        }
        
        output = format_storage_info(info)
        assert '/path/to/database.db' in output
        assert '0' in output

