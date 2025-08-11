"""
Tests for SemanticExtractor - Documentation-based semantic understanding
"""

import pytest
import json
import subprocess
from unittest.mock import Mock, patch, MagicMock
from redis_ai_patterns.semantic import SemanticExtractor


class TestSemanticExtractor:

    @pytest.fixture
    def mock_redis(self):
        with patch("redis.Redis") as mock:
            mock_client = Mock()
            mock.return_value = mock_client
            yield mock_client

    @pytest.fixture
    def extractor(self, mock_redis):
        return SemanticExtractor(namespace="test_semantic")

    def test_initialization(self, extractor):
        """Test proper initialization with patterns"""
        assert "navigation" in extractor.semantic_patterns
        assert "editing" in extractor.semantic_patterns
        assert "file_operations" in extractor.semantic_patterns
        assert "buffer_management" in extractor.semantic_patterns
        assert "search_replace" in extractor.semantic_patterns

    def test_pattern_structure(self, extractor):
        """Test semantic pattern structure"""
        nav_pattern = extractor.semantic_patterns["navigation"]
        assert "keywords" in nav_pattern
        assert "patterns" in nav_pattern
        assert isinstance(nav_pattern["keywords"], list)
        assert isinstance(nav_pattern["patterns"], list)

    @patch("subprocess.run")
    def test_extract_from_help_success(self, mock_subprocess, extractor):
        """Test successful help extraction"""
        # Mock successful subprocess call
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "forward-char moves the cursor forward by one character"
        mock_subprocess.return_value = mock_result

        result = extractor.extract_from_help("forward-char")

        assert result["topic"] == "forward-char"
        assert "navigation" in result["categories"]
        assert result["confidence"] > 0
        assert "forward" in result["raw_text"]

    @patch("subprocess.run")
    def test_extract_from_help_failure(self, mock_subprocess, extractor):
        """Test help extraction failure"""
        # Mock failed subprocess call
        mock_result = Mock()
        mock_result.returncode = 1
        mock_subprocess.return_value = mock_result

        result = extractor.extract_from_help("nonexistent-function")

        assert result["topic"] == "nonexistent-function"
        assert result["categories"] == []
        assert result["confidence"] == 0.0

    @patch("subprocess.run")
    def test_extract_from_help_timeout(self, mock_subprocess, extractor):
        """Test help extraction timeout"""
        mock_subprocess.side_effect = subprocess.TimeoutExpired("emacs", 10)

        result = extractor.extract_from_help("timeout-function")

        assert result["confidence"] == 0.0

    def test_parse_help_text_navigation(self, extractor):
        """Test parsing help text for navigation functions"""
        help_text = "Move point forward by one character. Forward means toward the end of the buffer."

        result = extractor._parse_help_text(help_text, "forward-char")

        assert "navigation" in result["categories"]
        assert result["confidence"] > 0

    def test_parse_help_text_editing(self, extractor):
        """Test parsing help text for editing functions"""
        help_text = "Insert text at point. Delete characters before point."

        result = extractor._parse_help_text(help_text, "insert-text")

        assert "editing" in result["categories"]

    def test_parse_help_text_multiple_categories(self, extractor):
        """Test parsing help text matching multiple categories"""
        help_text = (
            "Search for text and replace it with new text. Move cursor to next match."
        )

        result = extractor._parse_help_text(help_text, "query-replace")

        assert "search_replace" in result["categories"]
        assert "navigation" in result["categories"]
        assert len(result["categories"]) >= 2

    @patch.object(SemanticExtractor, "extract_from_help")
    def test_build_taxonomy(self, mock_extract, extractor, mock_redis):
        """Test building complete taxonomy"""
        # Mock extract_from_help responses
        mock_extract.side_effect = [
            {"topic": "forward-char", "categories": ["navigation"], "confidence": 0.8},
            {"topic": "insert-text", "categories": ["editing"], "confidence": 0.9},
            {
                "topic": "find-file",
                "categories": ["file_operations"],
                "confidence": 0.7,
            },
        ]

        functions = ["forward-char", "insert-text", "find-file"]
        taxonomy = extractor.build_taxonomy(functions)

        assert "navigation" in taxonomy
        assert "editing" in taxonomy
        assert "file_operations" in taxonomy

        # Check structure
        nav_items = taxonomy["navigation"]
        assert len(nav_items) == 1
        assert nav_items[0]["function"] == "forward-char"
        assert nav_items[0]["confidence"] == 0.8

        # Should store each function's semantic info
        assert mock_redis.set.call_count == 4  # One for each function + taxonomy

    def test_classify_intent_navigation(self, extractor):
        """Test intent classification for navigation"""
        result = extractor.classify_intent("move cursor forward")

        assert result["intent"] == "navigation"
        assert result["confidence"] > 0
        assert "navigation" in result["alternatives"]

    def test_classify_intent_editing(self, extractor):
        """Test intent classification for editing"""
        result = extractor.classify_intent("insert some text here")

        assert result["intent"] == "editing"
        assert result["confidence"] > 0

    def test_classify_intent_file_ops(self, extractor):
        """Test intent classification for file operations"""
        result = extractor.classify_intent("open a file")

        assert result["intent"] == "file_operations"
        assert result["confidence"] > 0

    def test_classify_intent_unknown(self, extractor):
        """Test intent classification for unknown input"""
        result = extractor.classify_intent("xyzabc nonsense")

        assert result["intent"] == "unknown"
        assert result["confidence"] == 0.0
        assert result["alternatives"] == {}

    def test_get_suggestions(self, extractor, mock_redis):
        """Test getting suggestions for a category"""
        # Mock stored taxonomy
        taxonomy = {
            "navigation": [
                {"function": "forward-char", "confidence": 0.9},
                {"function": "backward-char", "confidence": 0.8},
                {"function": "next-line", "confidence": 0.7},
            ]
        }

        mock_redis.get.return_value = json.dumps(taxonomy)

        suggestions = extractor.get_suggestions("navigation", limit=2)

        assert len(suggestions) == 2
        assert suggestions[0]["function"] == "forward-char"  # Highest confidence first
        assert suggestions[1]["function"] == "backward-char"

    def test_get_suggestions_empty_category(self, extractor, mock_redis):
        """Test getting suggestions for empty/unknown category"""
        mock_redis.get.return_value = None

        suggestions = extractor.get_suggestions("unknown_category")
        assert suggestions == []

    def test_analyze_usage_patterns(self, extractor, mock_redis):
        """Test analyzing usage patterns from Redis streams"""
        # Mock stream events
        mock_events = [
            ("event1", {"command": "forward-char"}),
            ("event2", {"command": "insert text"}),
            ("event3", {"command": "save file"}),
            ("event4", {"command": "forward-char"}),  # Repeat
        ]
        mock_redis.xrevrange.return_value = mock_events

        result = extractor.analyze_usage_patterns("test_session")

        assert "most_used_categories" in result
        assert "most_used_commands" in result
        assert result["total_commands"] == 4
        assert result["session_id"] == "test_session"

        # Should have classified some commands
        categories = result["most_used_categories"]
        commands = result["most_used_commands"]

        assert commands["forward-char"] == 2  # Used twice
        assert "navigation" in categories  # forward-char classified as navigation

    def test_analyze_usage_patterns_error(self, extractor, mock_redis):
        """Test usage pattern analysis with Redis error"""
        mock_redis.xrevrange.side_effect = Exception("Redis error")

        result = extractor.analyze_usage_patterns("test_session")

        assert "error" in result

    def test_suggest_workflow_improvements(self, extractor):
        """Test workflow improvement suggestions"""
        usage_patterns = {
            "most_used_categories": {
                "navigation": 15,  # High navigation usage
                "file_operations": 8,  # High file ops
                "editing": 20,  # Very high editing
            }
        }

        suggestions = extractor.suggest_workflow_improvements(usage_patterns)

        assert len(suggestions) >= 2  # Should suggest multiple improvements

        # Check for specific suggestions based on usage
        suggestion_text = " ".join(suggestions)
        assert (
            "navigation" in suggestion_text or "keyboard shortcuts" in suggestion_text
        )
        assert "editing" in suggestion_text or "snippets" in suggestion_text

    def test_suggest_workflow_improvements_low_usage(self, extractor):
        """Test workflow suggestions with low usage"""
        usage_patterns = {
            "most_used_categories": {"navigation": 2, "editing": 3}  # Low usage
        }

        suggestions = extractor.suggest_workflow_improvements(usage_patterns)

        # Should have fewer or no suggestions for low usage
        assert len(suggestions) <= 1
