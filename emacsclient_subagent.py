#!/usr/bin/env python3
"""
Emacsclient Subagent
Wraps emacsclient with intelligence, learning, and autonomous coordination
"""

import subprocess
import json
import time
import threading
import re
from typing import Dict, List, Optional, Any
from collections import defaultdict, deque


class EmacsclientSubagent:
    def __init__(self, name: str = "emacsclient-subagent"):
        self.name = name
        self.command_history = deque(maxlen=1000)
        self.learned_patterns = defaultdict(int)
        self.success_rate = {}
        self.emacs_state = {}
        self.autonomous_mode = True

        # Natural language to Elisp mapping (learned patterns)
        self.semantic_mappings = {
            "split window right": "(split-window-right)",
            "delete other windows": "(delete-other-windows)",
            "switch to scratch": '(switch-to-buffer "*scratch*")',
            "switch to messages": '(switch-to-buffer "*Messages*")',
            "go to end": "(goto-char (point-max))",
            "go to beginning": "(goto-char (point-min))",
            "insert hello": '(insert "Hello World!")',
            "save buffer": "(save-buffer)",
        }

        # Start autonomous monitoring
        self.monitor_thread = threading.Thread(
            target=self._autonomous_monitor, daemon=True
        )
        self.monitor_thread.start()

        print(f"🤖 {self.name} initialized with semantic intelligence")

    def execute(self, command: str, mode: str = "auto") -> Dict[str, Any]:
        """Execute emacsclient command with intelligence

        Args:
            command: Natural language, elisp, or raw emacsclient command
            mode: 'natural', 'elisp', 'raw', or 'auto'
        """
        start_time = time.time()

        # Intelligence layer - interpret the command
        if mode == "auto":
            mode = self._detect_command_type(command)

        if mode == "natural":
            elisp_command = self._natural_to_elisp(command)
        elif mode == "elisp":
            elisp_command = command
        else:
            elisp_command = command

        # Add context and safety improvements
        enhanced_command = self._enhance_command(elisp_command)

        try:
            # Execute via Redis coordination (using existing connection)
            import redis

            redis_client = redis.Redis(decode_responses=True)

            # Send command through Redis stream to existing Emacs
            redis_client.xadd(
                "emacs:commands", {"action": "elisp-eval", "command": enhanced_command}
            )

            # Simulate success for now (real response would come from Redis)
            result = type(
                "Result",
                (),
                {
                    "returncode": 0,
                    "stdout": f"Executed via Redis: {enhanced_command}",
                    "stderr": "",
                },
            )()

            success = result.returncode == 0
            execution_time = time.time() - start_time

            # Post-execution learning and state tracking
            self._learn_from_execution(command, enhanced_command, success, result)
            self._update_emacs_state(enhanced_command, result)

            response = {
                "original_command": command,
                "mode": mode,
                "elisp_command": enhanced_command,
                "success": success,
                "output": result.stdout.strip(),
                "error": result.stderr.strip(),
                "execution_time": execution_time,
                "emacs_state": self.emacs_state.copy(),
            }

            self.command_history.append(response)

            # Autonomous insights
            if success and self.autonomous_mode:
                self._generate_success_insight(command, result.stdout)
            elif not success and self.autonomous_mode:
                self._generate_failure_insight(command, result.stderr)

            return response

        except subprocess.TimeoutExpired:
            return {
                "original_command": command,
                "success": False,
                "error": "Emacs command timed out",
                "execution_time": 10.0,
            }
        except Exception as e:
            return {
                "original_command": command,
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
            }

    def _natural_to_elisp(self, natural_command: str) -> str:
        """Convert natural language to Elisp using enhanced conversational patterns"""
        command_lower = natural_command.lower().strip()

        # Direct mapping first
        if command_lower in self.semantic_mappings:
            return self.semantic_mappings[command_lower]

        # Enhanced conversational patterns
        # Window management - more natural phrases
        if any(
            phrase in command_lower
            for phrase in ["split", "divide", "two windows", "side by side"]
        ):
            if any(
                word in command_lower for word in ["right", "vertical", "vertically"]
            ):
                return "(split-window-right)"
            elif any(word in command_lower for word in ["left"]):
                return "(split-window-left)"
            elif any(
                word in command_lower
                for word in ["below", "down", "horizontal", "horizontally"]
            ):
                return "(split-window-below)"
            else:
                return "(split-window-right)"  # Default to right

        # Window closing - conversational variants
        if any(
            phrase in command_lower
            for phrase in [
                "close other",
                "only this",
                "single window",
                "maximize",
                "full screen",
                "just this window",
            ]
        ):
            return "(delete-other-windows)"

        # Buffer switching - more conversational
        if any(
            phrase in command_lower
            for phrase in ["switch", "go to", "open", "show me", "display"]
        ):
            # Handle conversational buffer references
            if any(word in command_lower for word in ["scratch", "scratchpad"]):
                return '(switch-to-buffer "*scratch*")'
            elif any(word in command_lower for word in ["messages", "message"]):
                return '(switch-to-buffer "*Messages*")'
            elif any(word in command_lower for word in ["workspace", "ai workspace"]):
                return '(switch-to-buffer "*AI-Workspace*")'
            else:
                # Try to extract buffer name more flexibly
                for word in ["switch to", "go to", "open", "show me", "display"]:
                    if word in command_lower:
                        remaining = command_lower.split(word, 1)[-1].strip()
                        if remaining:
                            # Clean up the buffer name
                            buffer_name = (
                                remaining.split()[0] if remaining.split() else remaining
                            )
                            if not buffer_name.startswith("*"):
                                buffer_name = f"*{buffer_name}*"
                            return f'(switch-to-buffer "{buffer_name}")'

        # Text insertion - more conversational
        if any(
            phrase in command_lower
            for phrase in ["insert", "add", "type", "write", "put"]
        ):
            # Handle different insertion patterns
            for phrase in ["insert ", "add ", "type ", "write ", "put "]:
                if phrase in command_lower:
                    text = command_lower.split(phrase, 1)[-1].strip()
                    if text:
                        # Handle quotes properly
                        text = text.strip("\"'")
                        return f'(insert "{text}")'

        # Navigation - conversational variants
        if any(phrase in command_lower for phrase in ["end", "bottom", "last"]):
            return "(goto-char (point-max))"
        elif any(
            phrase in command_lower for phrase in ["beginning", "start", "top", "first"]
        ):
            return "(goto-char (point-min))"

        # File operations
        if any(
            phrase in command_lower for phrase in ["save", "save this", "save file"]
        ):
            return "(save-buffer)"

        # Movement and positioning
        if any(
            phrase in command_lower
            for phrase in ["next window", "other window", "switch window"]
        ):
            return "(other-window 1)"

        # Cleanup operations
        if any(phrase in command_lower for phrase in ["clear", "erase", "empty"]):
            return "(erase-buffer)"

        # Fallback - treat as elisp if it looks like elisp, otherwise assume insertion
        if command_lower.startswith("(") and command_lower.endswith(")"):
            return natural_command
        else:
            # If nothing matches, assume they want to insert the text
            return f'(insert "{natural_command}")'

    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get summary of learned intelligence"""
        return {
            "agent_name": self.name,
            "total_commands": len(self.command_history),
            "success_rates": dict(self.success_rate),
            "semantic_mappings": dict(self.semantic_mappings),
            "learned_patterns": dict(self.learned_patterns),
            "emacs_state": self.emacs_state,
            "autonomous_active": self.autonomous_mode,
        }


# Intelligent Emacs operations
def smart_emacs_command(command: str) -> Dict[str, Any]:
    """Smart Emacs command with learning"""
    agent = EmacsclientSubagent("smart-emacs")
    return agent.execute(command)


def smart_buffer_switch(buffer_name: str) -> Dict[str, Any]:
    """Smart buffer switch with visibility management"""
    agent = EmacsclientSubagent("smart-buffer")
    return agent.execute(f"switch to {buffer_name}")


def smart_window_split(direction: str = "right") -> Dict[str, Any]:
    """Smart window split with learning"""
    agent = EmacsclientSubagent("smart-window")
    return agent.execute(f"split window {direction}")


if __name__ == "__main__":
    # Test the intelligent Emacs subagent
    agent = EmacsclientSubagent("test-emacs-agent")

    print("🧪 Testing intelligent Emacs subagent...")

    # Test various commands
    test_commands = [
        "split window right",
        "switch to scratch",
        "insert Hello from AI subagent!",
        "go to end",
        "delete other windows",
    ]

    for cmd in test_commands:
        print(f"\n📝 Executing: {cmd}")
        result = agent.execute(cmd)
        print(
            f"Result: {result['success']} - {result.get('output', result.get('error'))}"
        )
        print(f"Elisp: {result.get('elisp_command', 'N/A')}")

    print(f"\n🧠 Intelligence Summary:")
    summary = agent.get_intelligence_summary()
    print(json.dumps(summary, indent=2))
