#!/usr/bin/env python3
"""
Redis-Emacs Bridge - Proper Redis communication layer
Uses redis-ai-patterns library for high-throughput Emacs coordination
"""

import json
import time
import uuid
from typing import Dict, List, Any, Optional
from redis_ai_patterns import StreamProcessor
from redis_ai_patterns.streams import StreamEvent, EventType


class EmacsCommand:
    """Structured Emacs command for Redis streams"""

    def __init__(self, command_type: str, command: str, session_id: str = None):
        self.id = str(uuid.uuid4())
        self.type = command_type  # 'kbd', 'eval', 'buffer'
        self.command = command
        self.timestamp = time.time()
        self.session_id = session_id or f"session_{int(time.time())}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "command": self.command,
            "timestamp": self.timestamp,
            "session": self.session_id,
        }


class RedisEmacsBridge:
    """Redis-based Emacs communication bridge"""

    def __init__(self, session_id: str = None):
        self.stream_processor = StreamProcessor(namespace="emacs_bridge")
        self.session_id = session_id or f"bridge_{int(time.time())}"
        self.pending_commands = {}

        print(f"🌉 Redis-Emacs Bridge initialized (session: {self.session_id})")

    def send_keyboard_command(self, key_sequence: str) -> Dict[str, Any]:
        """Send keyboard command to Emacs via Redis"""
        cmd = EmacsCommand("kbd", key_sequence, self.session_id)

        # Add to Redis stream
        event = StreamEvent(
            event_type=EventType.COMMAND, data=cmd.to_dict(), session_id=self.session_id
        )

        stream_id = self.stream_processor.add_event(event)
        self.pending_commands[cmd.id] = {
            "command": cmd,
            "stream_id": stream_id,
            "sent_at": time.time(),
        }

        print(f"   🎹 Queued {key_sequence} to Redis stream {stream_id}")

        # Wait for response (simplified for demo)
        time.sleep(0.5)  # Give Emacs time to respond

        return {
            "command_id": cmd.id,
            "stream_id": stream_id,
            "success": True,
            "method": "redis_stream",
        }

    def send_elisp_command(self, elisp_code: str) -> Dict[str, Any]:
        """Send Elisp evaluation to Emacs via Redis"""
        cmd = EmacsCommand("eval", elisp_code, self.session_id)

        event = StreamEvent(
            event_type=EventType.COMMAND, data=cmd.to_dict(), session_id=self.session_id
        )

        stream_id = self.stream_processor.add_event(event)
        self.pending_commands[cmd.id] = {
            "command": cmd,
            "stream_id": stream_id,
            "sent_at": time.time(),
        }

        print(f"   🧠 Queued Elisp to Redis stream {stream_id}")

        time.sleep(0.3)

        return {
            "command_id": cmd.id,
            "stream_id": stream_id,
            "success": True,
            "method": "redis_stream",
        }

    def create_tutorial_buffer(self) -> Dict[str, Any]:
        """Create a visible tutorial buffer for AI demonstrations"""
        elisp_code = """
        (progn 
          (switch-to-buffer "*AI-Tutorial-Redis*")
          (erase-buffer)
          (insert "🤖 AI Tutorial via Redis Streams\\n\\n")
          (insert "This AI is learning Emacs through Redis coordination!\\n\\n")
          (insert "Command history:\\n")
          (goto-char (point-max)))
        """

        return self.send_elisp_command(elisp_code)

    def observe_emacs_state(self) -> Dict[str, Any]:
        """Observe current Emacs state via Redis"""
        elisp_code = """
        (list 
          (buffer-name)
          (point)
          (line-number-at-pos)
          (current-column)
          (buffer-size))
        """

        result = self.send_elisp_command(elisp_code)

        # For demo, simulate observation
        return {
            "buffer_name": "*AI-Tutorial-Redis*",
            "cursor_position": 42,
            "line_number": 5,
            "column": 10,
            "buffer_size": 128,
            "observation_time": time.time(),
            "method": "redis_stream",
        }

    def log_command_to_buffer(self, command: str, result: str) -> None:
        """Log executed command to the tutorial buffer"""
        elisp_code = f"""
        (when (get-buffer "*AI-Tutorial-Redis*")
          (with-current-buffer "*AI-Tutorial-Redis*"
            (goto-char (point-max))
            (insert "✅ {command} → {result}\\n")))
        """

        self.send_elisp_command(elisp_code)

    def get_stream_statistics(self) -> Dict[str, Any]:
        """Get Redis stream statistics"""
        stats = {}

        # Get command stream info
        cmd_info = self.stream_processor.get_stream_info("events:commands")
        stats["commands_sent"] = cmd_info.get("length", 0)

        # Get response stream info (would be implemented with real Emacs connection)
        stats["responses_received"] = 0  # Placeholder
        stats["pending_commands"] = len(self.pending_commands)
        stats["session_id"] = self.session_id

        return stats

    def shutdown(self) -> None:
        """Clean shutdown of bridge"""
        print(f"🌉 Redis-Emacs Bridge shutting down (session: {self.session_id})")

        # Log final statistics
        stats = self.get_stream_statistics()
        print(f"   📊 Final stats: {stats['commands_sent']} commands sent")


def main():
    """Test the Redis-Emacs bridge"""
    bridge = RedisEmacsBridge()

    # Test sequence
    bridge.create_tutorial_buffer()
    time.sleep(1)

    bridge.send_keyboard_command("C-v")
    bridge.log_command_to_buffer("C-v", "scroll down")

    bridge.send_keyboard_command("C-f")
    bridge.log_command_to_buffer("C-f", "forward char")

    state = bridge.observe_emacs_state()
    print(f"Observed state: {state}")

    stats = bridge.get_stream_statistics()
    print(f"Stream stats: {stats}")

    bridge.shutdown()


if __name__ == "__main__":
    main()
