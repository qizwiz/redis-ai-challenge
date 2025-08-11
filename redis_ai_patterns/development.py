"""
Development Assistant - AI-powered development tools
"""

import redis
import json
import time
import re
from typing import Dict, List, Any, Optional
from .core import RedisAIBase


class DevAssistant(RedisAIBase):
    """AI-powered development assistance tools"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def analyze_code_context(
        self, buffer_content: str, cursor_position: int, language: str = "python"
    ) -> Dict[str, Any]:
        """Analyze code context around cursor position"""
        lines = buffer_content.split("\n")
        cursor_line = self._get_cursor_line(lines, cursor_position)

        context = {
            "current_line": lines[cursor_line] if cursor_line < len(lines) else "",
            "surrounding_lines": self._get_surrounding_lines(lines, cursor_line),
            "language": language,
            "cursor_position": cursor_position,
            "analysis_timestamp": time.time(),
        }

        # Store context for AI processing
        self.store_json(f"context:{self.session_id}", context)

        return context

    def _get_cursor_line(self, lines: List[str], cursor_position: int) -> int:
        """Helper to get the 0-based line number of the cursor position."""
        total_chars = 0
        for i, line in enumerate(lines):
            total_chars += len(line) + 1  # +1 for the newline character
            if total_chars > cursor_position:
                return i
        return len(lines) - 1  # Should not happen if cursor_position is valid

    def _get_surrounding_lines(
        self, lines: List[str], cursor_line: int, context_size: int = 3
    ) -> Dict[str, List[str]]:
        """Helper to get surrounding lines for context."""
        before_lines = lines[max(0, cursor_line - context_size) : cursor_line]
        current_line = lines[cursor_line] if 0 <= cursor_line < len(lines) else ""
        after_lines = lines[
            cursor_line + 1 : min(len(lines), cursor_line + context_size + 1)
        ]
        return {"before": before_lines, "current": current_line, "after": after_lines}

    def detect_potential_issues(
        self, code_snippet: str, language: str = "python"
    ) -> List[Dict[str, Any]]:
        """Detect potential code issues"""
        issues = []

        # Simple pattern-based detection
        if language == "python":
            # Check for common issues
            if "import *" in code_snippet:
                issues.append(
                    {
                        "type": "style",
                        "severity": "warning",
                        "message": "Avoid wildcard imports",
                        "suggestion": "Import specific functions/classes",
                    }
                )

            if re.search(r"except:", code_snippet):
                issues.append(
                    {
                        "type": "error_handling",
                        "severity": "warning",
                        "message": "Bare except clause",
                        "suggestion": "Specify exception types",
                    }
                )

        # Store issues for tracking
        if issues:
            self.store_json(f"issues:{self.session_id}:{int(time.time())}", issues)

        return issues

    def suggest_completion(
        self, partial_code: str, context: Dict[str, Any]
    ) -> List[str]:
        """Suggest code completions based on context"""
        # Simple completion suggestions
        suggestions = []

        language = context.get("language", "python")

        if language == "python":
            # Basic Python completions
            if partial_code.endswith("."):
                suggestions = ["append(", "insert(", "remove(", "pop()", "clear()"]
            elif "def " in partial_code:
                suggestions = ["def function_name():", "def __init__(self):"]
            elif "class " in partial_code:
                suggestions = ["class ClassName:", "class ClassName(object):"]

        # Store suggestions for learning
        completion_data = {
            "partial_code": partial_code,
            "suggestions": suggestions,
            "context": context,
            "timestamp": time.time(),
        }
        self.store_json(
            f"completions:{self.session_id}:{int(time.time())}", completion_data
        )

        return suggestions

    def monitor_keystroke_patterns(
        self, time_window_seconds: int = 10
    ) -> Dict[str, Any]:
        """Monitor recent keystroke patterns for AI assistance"""
        try:
            # Get recent keystrokes from stream
            end_time = int(time.time() * 1000)
            start_time = end_time - (time_window_seconds * 1000)

            events = self.redis_client.xrevrange(
                self.key("events:keystrokes"), min=start_time, max=end_time, count=100
            )

            patterns = {
                "keystroke_count": len(events),
                "time_window": time_window_seconds,
                "patterns_detected": [],
                "suggestions": [],
            }

            # Analyze patterns
            if len(events) > 20:
                patterns["patterns_detected"].append("high_typing_frequency")
                patterns["suggestions"].append("Consider using snippets or templates")

            return patterns

        except Exception as e:
            return {"error": str(e)}

    def provide_contextual_help(
        self, current_buffer: str, cursor_line: int, language: str = "python"
    ) -> Dict[str, Any]:
        """Provide contextual help based on current code"""
        lines = current_buffer.split("\n")
        current_line_text = lines[cursor_line] if cursor_line < len(lines) else ""

        help_info = {
            "current_line": current_line_text,
            "line_number": cursor_line,
            "language": language,
            "help_suggestions": [],
            "related_functions": [],
        }

        # Basic help based on current line
        if language == "python":
            if "import" in current_line_text:
                help_info["help_suggestions"].append(
                    "Use specific imports instead of wildcards"
                )
            elif "def " in current_line_text:
                help_info["help_suggestions"].append(
                    "Add docstring for function documentation"
                )
            elif "class " in current_line_text:
                help_info["help_suggestions"].append(
                    "Consider inheritance and composition patterns"
                )

        return help_info

    def get_system_status(self) -> Dict[str, Any]:
        """Get development assistant system status"""
        status = {
            "redis_connected": self.ping(),
            "session_id": self.session_id,
            "namespace": self.namespace,
            "timestamp": time.time(),
        }

        # Get some statistics
        try:
            # Count stored contexts
            context_keys = self.redis_client.keys(self.key("context:*"))
            status["stored_contexts"] = len(context_keys)

            # Check stream lengths
            for stream_name in ["events:keystrokes", "events:commands"]:
                try:
                    stream_info = self.redis_client.xinfo_stream(self.key(stream_name))
                    status[f"{stream_name}_length"] = stream_info.get("length", 0)
                except:
                    status[f"{stream_name}_length"] = 0

        except Exception as e:
            status["stats_error"] = str(e)

        return status
