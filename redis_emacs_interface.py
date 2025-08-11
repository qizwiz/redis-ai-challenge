#!/usr/bin/env python3
"""
Simple Redis-Emacs Interface
Just send the right messages in the right order - no Lisp needed!
"""

import redis
import fastmcp


class RedisEmacsInterface:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

        # Command mapping - action to what it actually means
        self.action_map = {
            # Window management
            "split-window-right": {"action": "split-window-right"},
            "split-window-left": {"action": "split-window-left"},
            "split-window-up": {"action": "split-window-up"},
            "split-window-down": {"action": "split-window-down"},
            "delete-other-windows": {"action": "delete-other-windows"},
            "delete-window": {"action": "delete-window"},
            "other-window": {"action": "other-window"},
            # Buffer operations
            "switch-to-buffer": {"action": "switch-to-buffer"},
            "kill-buffer": {"action": "kill-buffer"},
            "save-buffer": {"action": "save-buffer"},
            # Text operations
            "insert-text": {"action": "insert-text"},
            "goto-char": {"action": "goto-char"},
            "beginning-of-buffer": {"action": "beginning-of-buffer"},
            "end-of-buffer": {"action": "end-of-buffer"},
            # Common patterns
            "scratch": {"action": "switch-to-buffer", "target": "*scratch*"},
            "messages": {"action": "switch-to-buffer", "target": "*Messages*"},
        }

    def send_command(self, action, **kwargs):
        """Send command to Emacs via Redis"""

        # Get base action
        if action in self.action_map:
            command_data = self.action_map[action].copy()
        else:
            command_data = {"action": action}

        # Add any additional parameters
        command_data.update(kwargs)

        # Send to Redis
        message_id = self.redis_client.xadd("emacs:commands", command_data)
        return message_id

    def natural_language_to_action(self, text):
        """Convert natural language to actions"""
        text_lower = text.lower()

        # Window operations
        if "split" in text_lower and "right" in text_lower:
            return "split-window-right"
        elif "split" in text_lower and "left" in text_lower:
            return "split-window-left"
        elif "split" in text_lower and ("up" in text_lower or "above" in text_lower):
            return "split-window-up"
        elif "split" in text_lower and ("down" in text_lower or "below" in text_lower):
            return "split-window-down"
        elif "delete other windows" in text_lower or "single window" in text_lower:
            return "delete-other-windows"
        elif "delete window" in text_lower:
            return "delete-window"
        elif "other window" in text_lower or "switch window" in text_lower:
            return "other-window"

        # Buffer operations
        elif "scratch" in text_lower:
            return "scratch"
        elif "messages" in text_lower:
            return "messages"
        elif "save" in text_lower:
            return "save-buffer"

        # Text operations
        elif "insert" in text_lower:
            # Extract text to insert
            if "insert" in text_lower:
                # Simple extraction - everything after "insert"
                parts = text_lower.split("insert", 1)
                if len(parts) > 1:
                    text_to_insert = parts[1].strip()
                    return ("insert-text", {"text": text_to_insert})

        elif "beginning" in text_lower or "start" in text_lower:
            return "beginning-of-buffer"
        elif "end" in text_lower:
            return "end-of-buffer"

        return action


# FastMCP Server
mcp = fastmcp.FastMCP("redis-emacs-interface")
interface = RedisEmacsInterface()


@mcp.tool()
def emacs_action(action: str, target: str = "", text: str = "") -> str:
    """Send action directly to Emacs via Redis

    Args:
        action: The action to perform (split-window-right, delete-other-windows, etc.)
        target: Target buffer name (optional)
        text: Text to insert (optional)
    """
    kwargs = {}
    if target:
        kwargs["target"] = target
    if text:
        kwargs["text"] = text

    message_id = interface.send_command(action, **kwargs)
    return f"✅ Sent action '{action}' to Emacs (message ID: {message_id})"


@mcp.tool()
def emacs_natural(command: str) -> str:
    """Send natural language command to Emacs via Redis

    Args:
        command: Natural language command (e.g., "split window right", "go to scratch")
    """
    result = interface.natural_language_to_action(command)

    if isinstance(result, tuple):
        action, kwargs = result
        message_id = interface.send_command(action, **kwargs)
    else:
        action = result
        message_id = interface.send_command(action)

    return f"✅ Executed '{command}' as action '{action}' (message ID: {message_id})"


@mcp.tool()
def emacs_window_split(direction: str) -> str:
    """Split window in specified direction

    Args:
        direction: right, left, up, or down
    """
    action = f"split-window-{direction}"
    message_id = interface.send_command(action)
    return f"✅ Split window {direction} (message ID: {message_id})"


@mcp.tool()
def emacs_single_window() -> str:
    """Return to single window (delete other windows)"""
    message_id = interface.send_command("delete-other-windows")
    return f"✅ Deleted other windows (message ID: {message_id})"


@mcp.tool()
def emacs_switch_buffer(buffer_name: str) -> str:
    """Switch to specified buffer

    Args:
        buffer_name: Name of buffer to switch to (e.g., "*scratch*", "*Messages*")
    """
    message_id = interface.send_command("switch-to-buffer", target=buffer_name)
    return f"✅ Switched to buffer '{buffer_name}' (message ID: {message_id})"


if __name__ == "__main__":
    print("🔗 Starting Redis-Emacs Interface FastMCP Server")
    fastmcp.run_stdio_async(mcp)
