"""
Tests for DevAssistant - AI-powered development tools
"""

import pytest
import json
import time
from unittest.mock import Mock, patch
from redis_ai_patterns.development import DevAssistant


class TestDevAssistant:

    @pytest.fixture
    def mock_redis(self):
        with patch("redis.Redis") as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def dev_assistant(self, mock_redis):
        return DevAssistant(namespace="test_dev")

    def test_initialization(self, dev_assistant):
        """Test proper initialization"""
        assert dev_assistant.namespace == "test_dev"
        assert dev_assistant.session_id.startswith("test_dev_")

    def test_analyze_code_context(self, dev_assistant, mock_redis):
        """Test code context analysis"""
        buffer_content = "def hello():\n    print('world')\n    return True"
        cursor_position = 15  # Position in first line

        context = dev_assistant.analyze_code_context(
            buffer_content, cursor_position, "python"
        )

        assert context["language"] == "python"
        assert context["cursor_position"] == 15
        assert (
            context["current_line"] == "    print('world')"
        )  # cursor is on second line
        assert "surrounding_lines" in context

        # Should store context in Redis
        mock_redis.set.assert_called_once()

    def test_get_cursor_line(self, dev_assistant):
        """Test cursor line calculation"""
        lines = ["line 1", "line 2", "line 3"]

        # Position 0 should be line 0
        assert dev_assistant._get_cursor_line(lines, 0) == 0

        # Position after first line should be line 1
        assert dev_assistant._get_cursor_line(lines, 8) == 1  # "line 1\n" = 7 chars + 1

        # Very large position should return last line
        assert dev_assistant._get_cursor_line(lines, 1000) == 2

    def test_get_surrounding_lines(self, dev_assistant):
        """Test getting surrounding lines for context"""
        lines = ["line 0", "line 1", "line 2", "line 3", "line 4"]
        cursor_line = 2

        surrounding = dev_assistant._get_surrounding_lines(
            lines, cursor_line, context_size=1
        )

        assert surrounding["before"] == ["line 1"]
        assert surrounding["current"] == "line 2"
        assert surrounding["after"] == ["line 3"]

    def test_get_surrounding_lines_edge_cases(self, dev_assistant):
        """Test surrounding lines at edges"""
        lines = ["line 0", "line 1", "line 2"]

        # At beginning
        surrounding = dev_assistant._get_surrounding_lines(lines, 0, context_size=2)
        assert surrounding["before"] == []
        assert surrounding["current"] == "line 0"
        assert len(surrounding["after"]) <= 2

        # At end
        surrounding = dev_assistant._get_surrounding_lines(lines, 2, context_size=2)
        assert len(surrounding["before"]) <= 2
        assert surrounding["current"] == "line 2"
        assert surrounding["after"] == []

    def test_detect_potential_issues_python(self, dev_assistant, mock_redis):
        """Test detecting Python code issues"""
        # Code with wildcard import
        code_with_wildcard = "from os import *\nprint('hello')"
        issues = dev_assistant.detect_potential_issues(code_with_wildcard, "python")

        assert len(issues) > 0
        assert any("wildcard" in issue["message"].lower() for issue in issues)
        assert issues[0]["type"] == "style"

        # Code with bare except
        code_with_bare_except = "try:\n    pass\nexcept:\n    pass"
        issues = dev_assistant.detect_potential_issues(code_with_bare_except, "python")

        assert len(issues) > 0
        assert any("bare except" in issue["message"].lower() for issue in issues)

    def test_detect_potential_issues_clean_code(self, dev_assistant, mock_redis):
        """Test detecting issues in clean code"""
        clean_code = "import os\ndef hello():\n    return 'world'"
        issues = dev_assistant.detect_potential_issues(clean_code, "python")

        assert len(issues) == 0

    def test_suggest_completion_python(self, dev_assistant, mock_redis):
        """Test Python code completion suggestions"""
        context = {"language": "python"}

        # Test method completion
        suggestions = dev_assistant.suggest_completion("mylist.", context)
        assert "append(" in suggestions
        assert "insert(" in suggestions

        # Test function definition
        suggestions = dev_assistant.suggest_completion("def ", context)
        assert any("def " in s for s in suggestions)

        # Test class definition
        suggestions = dev_assistant.suggest_completion("class ", context)
        assert any("class " in s for s in suggestions)

        # Should store completion data
        mock_redis.set.assert_called()

    def test_suggest_completion_other_languages(self, dev_assistant, mock_redis):
        """Test completion for non-Python languages"""
        context = {"language": "javascript"}

        suggestions = dev_assistant.suggest_completion("obj.", context)
        # Should return empty list for unsupported languages currently
        assert isinstance(suggestions, list)

    def test_monitor_keystroke_patterns(self, dev_assistant, mock_redis):
        """Test monitoring keystroke patterns"""
        # Mock Redis stream response
        mock_events = [f"event_{i}" for i in range(25)]  # 25 events = high frequency
        mock_redis.xrevrange.return_value = mock_events

        patterns = dev_assistant.monitor_keystroke_patterns(time_window_seconds=5)

        assert patterns["keystroke_count"] == 25
        assert patterns["time_window"] == 5
        assert "high_typing_frequency" in patterns["patterns_detected"]
        assert any(
            "snippets" in suggestion.lower() for suggestion in patterns["suggestions"]
        )

    def test_monitor_keystroke_patterns_low_activity(self, dev_assistant, mock_redis):
        """Test monitoring with low keystroke activity"""
        mock_redis.xrevrange.return_value = ["event1", "event2"]  # Low activity

        patterns = dev_assistant.monitor_keystroke_patterns()

        assert patterns["keystroke_count"] == 2
        assert patterns["patterns_detected"] == []  # No patterns for low activity

    def test_monitor_keystroke_patterns_error(self, dev_assistant, mock_redis):
        """Test keystroke monitoring with Redis error"""
        mock_redis.xrevrange.side_effect = Exception("Redis connection error")

        patterns = dev_assistant.monitor_keystroke_patterns()

        assert "error" in patterns

    def test_provide_contextual_help_python(self, dev_assistant):
        """Test providing contextual help for Python"""
        buffer_content = (
            "import os\ndef my_function():\n    pass\nclass MyClass:\n    pass"
        )

        # Help for import line
        help_info = dev_assistant.provide_contextual_help(buffer_content, 0, "python")
        assert "import" in help_info["help_suggestions"][0].lower()

        # Help for function definition line
        help_info = dev_assistant.provide_contextual_help(buffer_content, 1, "python")
        assert "docstring" in help_info["help_suggestions"][0].lower()

        # Help for class definition line
        help_info = dev_assistant.provide_contextual_help(buffer_content, 3, "python")
        assert "inheritance" in help_info["help_suggestions"][0].lower()

    def test_provide_contextual_help_empty_line(self, dev_assistant):
        """Test contextual help for empty or non-existent lines"""
        buffer_content = "line 1\nline 2"

        # Line beyond buffer
        help_info = dev_assistant.provide_contextual_help(buffer_content, 10, "python")
        assert help_info["current_line"] == ""
        assert help_info["line_number"] == 10

    def test_get_system_status(self, dev_assistant, mock_redis):
        """Test getting system status"""
        # Mock Redis responses
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = ["key1", "key2", "key3"]

        # Mock stream info
        stream_info = {"length": 42}
        mock_redis.xinfo_stream.return_value = stream_info

        status = dev_assistant.get_system_status()

        assert status["redis_connected"] is True
        assert status["session_id"] == dev_assistant.session_id
        assert status["namespace"] == "test_dev"
        assert status["stored_contexts"] == 3
        assert "timestamp" in status

        # Should check multiple streams
        assert mock_redis.xinfo_stream.call_count >= 1

    def test_get_system_status_redis_error(self, dev_assistant, mock_redis):
        """Test system status with Redis errors"""
        mock_redis.ping.return_value = False
        mock_redis.keys.side_effect = Exception("Redis error")

        status = dev_assistant.get_system_status()

        assert status["redis_connected"] is False or "stats_error" in status
        assert "stats_error" in status

    def test_get_system_status_stream_errors(self, dev_assistant, mock_redis):
        """Test system status with stream info errors"""
        mock_redis.ping.return_value = True
        mock_redis.keys.return_value = []
        mock_redis.xinfo_stream.side_effect = Exception("Stream error")

        status = dev_assistant.get_system_status()

        # Should handle stream errors gracefully
        assert "events:keystrokes_length" in status
        assert status["events:keystrokes_length"] == 0  # Default value on error
