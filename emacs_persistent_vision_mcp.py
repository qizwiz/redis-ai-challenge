#!/usr/bin/env python3
"""
Emacs Persistent Vision MCP Server
Real-time bidirectional Emacs control with persistent visual awareness
"""

import asyncio
import json
import redis
import time
from typing import Any, Dict, List, Optional, Union
from fastmcp import FastMCP
import logging
import sys # Added import sys

# Configure logging to go to stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr,
                    format='[%(asctime)s] %(levelname)s: %(message)s')
# Suppress FastMCP's default stdout handler if it exists
for handler in logging.root.handlers[:]:
    if isinstance(handler, logging.StreamHandler) and handler.stream == sys.stdout:
        logging.root.removeHandler(handler)


class EmacsPersistentVisionMCP:
    def __init__(self):
        """Initialize the Emacs persistent vision MCP server"""
        try:
            self.redis_client = redis.Redis(decode_responses=True, socket_timeout=2)
            self.redis_client.ping()
        except Exception as e:
            raise Exception(f"Redis connection failed: {e}")

        self.session_prefix = "emacs_"

    def get_active_session(self) -> Optional[str]:
        """Get the currently active Emacs session"""
        try:
            
            
            for session_id, data in instances.items():
                if session_id.startswith(self.session_prefix):
                    # Check if session is recent (last heartbeat within 60 seconds)
                    try:
                        session_data = json.loads(data)
                        # For now, return the first active session
                        return session_id
                    except:
                        continue
            return None
        except:
            return None

    def get_live_state(self) -> Dict:
        """Get the current live state of Emacs"""
        try:
            state_json = self.redis_client.get("emacs:live_state")
            if state_json:
                return json.loads(state_json)
            return {}
        except:
            return {}

    def send_command(self, command_type: str, command_data: Union[str, Dict]) -> str:
        """Send a command directly to Emacs daemon"""
        try:
            if command_type == "elisp":
                # Route directly to the redis-tutorial daemon that has the bridge
                import subprocess
                result = subprocess.run([
                    "emacsclient", "-s", "redis-tutorial", "-e", command_data
                ], capture_output=True, text=True, timeout=5)
                
                if result.returncode == 0:
                    return f"✅ Daemon executed: {result.stdout.strip()}"
                else:
                    # Fallback to Redis stream
                    command_id = self.redis_client.xadd(
                        "emacs:commands", {"elisp": command_data}
                    )
                    return f"⚠️ Fallback to stream: {command_id}"
            elif command_type == "function":
                if isinstance(command_data, dict):
                    command_id = self.redis_client.xadd("emacs:commands", command_data)
                else:
                    command_id = self.redis_client.xadd(
                        "emacs:commands", {"command": command_data}
                    )
            else:
                raise ValueError(f"Unknown command type: {command_type}")

            return f"Command sent: {command_id}"
        except Exception as e:
            return f"Error sending command: {e}"

    def get_recent_changes(self, count: int = 5) -> List[Dict]:
        """Get recent vision changes"""
        try:
            events = self.redis_client.xrevrange("emacs:vision", count=count)
            changes = []
            for event_id, fields in events:
                try:
                    changes.append(
                        {
                            "id": event_id,
                            "session": fields.get("session", "unknown"),
                            "timestamp": float(fields.get("timestamp", 0)),
                            "changes": json.loads(fields.get("changes", "null")),
                            "state": json.loads(fields.get("state", "{}")),
                        }
                    )
                except:
                    continue
            return changes
        except:
            return []


# Create FastMCP instance
mcp = FastMCP("emacs-persistent-vision")
emacs_vision = EmacsPersistentVisionMCP()


@mcp.tool()
def get_emacs_state() -> str:
    """
    Get the current real-time state of Emacs with persistent vision.

    Returns:
        Complete current state including buffer, cursor position, windows, etc.
    """
    state = emacs_vision.get_live_state()
    if not state:
        response_content = "❌ No live Emacs state available. Is the Redis executor running?"
        
        return response_content

    session = emacs_vision.get_active_session()

    response_content = f"""🔴 LIVE EMACS STATE 🔴
Session: {session or 'Unknown'}
Current Buffer: {state.get('buffer', 'Unknown')}
Cursor: Line {state.get('line', '?')}, Column {state.get('column', '?')}, Position {state.get('cursor', '?')}
Buffer Size: {state.get('size', '?')} characters
Window Count: {state.get('windows', '?')}
Visible Buffers: {state.get('visible-buffers', [])}
Frame Count: {state.get('frames', '?')}
Mode: {state.get('mode', 'Unknown')}
Modified: {state.get('modified', False)}
Region Active: {state.get('region-active', False)}
Content Hash: {state.get('content-hash', 'Unknown')[:8]}...
Last Update: {time.strftime('%H:%M:%S', time.localtime(state.get('timestamp', 0)))}

✅ Persistent vision is active - state updates in real-time"""
    
    return response_content

def _execute_elisp_impl(code: str) -> str:
    """Internal implementation of elisp execution"""
    if not code.strip():
        return "❌ Empty Elisp code provided"

    # Send the command
    result = emacs_vision.send_command("elisp", code)

    # Get immediate state feedback
    time.sleep(0.2)  # Brief pause for command execution
    state = emacs_vision.get_live_state()

    return f"""✅ Elisp Executed: {code}

{result}

📊 Current State After Execution:
Buffer: {state.get('buffer', 'Unknown')}
Cursor: Line {state.get('line', '?')}, Position {state.get('cursor', '?')}
Windows: {state.get('visible-buffers', [])}
Last Update: {time.strftime('%H:%M:%S', time.localtime(state.get('timestamp', 0)))}"""


@mcp.tool()
def execute_elisp(code: str) -> str:
    """
    Execute Elisp code directly in Emacs with immediate visual feedback.

    Args:
        code: The Elisp expression to execute (e.g., "(message \"Hello World\")")

    Returns:
        Confirmation that the command was sent and current state
    """
    return _execute_elisp_impl(code)



@mcp.tool()
def switch_buffer(buffer_name: str) -> str:
    """
    Switch to a specific buffer in Emacs.

    Args:
        buffer_name: Name of the buffer to switch to (e.g., "*scratch*")

    Returns:
        Confirmation and new state
    """
    code = f'(switch-to-buffer "{buffer_name}")'
    return _execute_elisp_impl(code)


@mcp.tool()
def create_buffer_with_content(buffer_name: str, content: str) -> str:
    """
    Create a new buffer with specific content.

    Args:
        buffer_name: Name of the new buffer
        content: Content to insert into the buffer

    Returns:
        Confirmation and new state
    """
    # Escape quotes in content
    escaped_content = content.replace('"', '\\"').replace("\n", "\\n")
    code = f'(progn (switch-to-buffer "{buffer_name}") (erase-buffer) (insert "{escaped_content}"))'
    return _execute_elisp_impl(code)


@mcp.tool()
def split_window(direction: str = "right") -> str:
    """
    Split the current window.

    Args:
        direction: Direction to split ("right", "below", "left", "above")

    Returns:
        Confirmation and new window state
    """
    if direction in ["right", "vertical"]:
        code = "(split-window-right)"
    elif direction in ["below", "horizontal"]:
        code = "(split-window-below)"
    else:
        return f"❌ Invalid direction: {direction}. Use 'right' or 'below'"

    return _execute_elisp_impl(code)


@mcp.tool()
def goto_line(line_number: int) -> str:
    """
    Move cursor to a specific line number.

    Args:
        line_number: Line number to move to

    Returns:
        Confirmation and new cursor position
    """
    code = f"(goto-line {line_number})"
    return _execute_elisp_impl(code)


@mcp.tool()
def insert_text(text: str) -> str:
    """
    Insert text at the current cursor position.

    Args:
        text: Text to insert

    Returns:
        Confirmation and updated state
    """
    # Escape quotes and newlines
    escaped_text = text.replace('"', '\\"').replace("\n", "\\n")
    code = f'(insert "{escaped_text}")'
    return _execute_elisp_impl(code)


@mcp.tool()
def get_vision_history(count: int = 5) -> str:
    """
    Get recent vision change history to see what happened in Emacs.

    Args:
        count: Number of recent changes to retrieve (default: 5)

    Returns:
        Recent change history with timestamps
    """
    changes = emacs_vision.get_recent_changes(count)

    if not changes:
        return "❌ No vision history available"

    history = ["📺 RECENT VISION HISTORY 📺", "=" * 40]

    for i, change in enumerate(changes, 1):
        timestamp = time.strftime("%H:%M:%S.%f", time.localtime(change["timestamp"]))[
            :12
        ]
        state = change["state"]
        changes_data = change["changes"]

        history.append(f"\n🕐 {timestamp} - Change #{i}")
        history.append(f"Buffer: {state.get('buffer', 'Unknown')}")
        history.append(
            f"Cursor: Line {state.get('line', '?')}, Position {state.get('cursor', '?')}"
        )
        history.append(f"Windows: {state.get('visible-buffers', [])}")

        if changes_data:
            if changes_data.get("buffer-changed"):
                history.append(
                    f"🔄 Buffer Changed: {changes_data.get('old-buffer')} → {changes_data.get('new-buffer')}"
                )
            if changes_data.get("cursor-moved"):
                history.append(
                    f"↗️ Cursor Moved: {changes_data.get('cursor-delta')} positions"
                )
            if changes_data.get("content-changed"):
                size_delta = changes_data.get("size-delta", 0)
                if size_delta > 0:
                    history.append(f"📝 Content Added: +{size_delta} characters")
                elif size_delta < 0:
                    history.append(f"🗑️ Content Removed: {size_delta} characters")
            if changes_data.get("windows-changed"):
                history.append(
                    f"🪟 Windows Changed: {changes_data.get('old-windows')} → {changes_data.get('new-windows')}"
                )

    return "\n".join(history)


@mcp.tool()
def emacs_health_check() -> str:
    """
    Check the health and status of the Emacs persistent vision system.

    Returns:
        Complete system health report
    """
    # Check Redis connection
    try:
        ping = emacs_vision.redis_client.ping()
        redis_status = "✅ Connected" if ping else "❌ Failed"
    except:
        redis_status = "❌ Connection Error"

    # Check active sessions
    session = emacs_vision.get_active_session()
    session_status = f"✅ Active: {session}" if session else "❌ No Active Session"

    # Check live state availability
    state = emacs_vision.get_live_state()
    state_status = "✅ Available" if state else "❌ No State Data"

    # Check vision stream activity
    try:
        recent_events = emacs_vision.redis_client.xrevrange("emacs:vision", count=1)
        if recent_events:
            last_event = recent_events[0]
            event_data = last_event[1]
            last_timestamp = float(event_data.get("timestamp", 0))
            time_ago = time.time() - last_timestamp
            if time_ago < 10:
                vision_status = f"✅ Active (last update {time_ago:.1f}s ago)"
            else:
                vision_status = f"⚠️ Stale (last update {time_ago:.1f}s ago)"
        else:
            vision_status = "❌ No Vision Events"
    except:
        vision_status = "❌ Vision Stream Error"

    # Check command queue
    try:
        queue_length = emacs_vision.redis_client.xlen("emacs:commands")
        queue_status = f"📊 {queue_length} commands queued"
    except:
        queue_status = "❌ Queue Error"

    return f"""🏥 EMACS PERSISTENT VISION HEALTH CHECK 🏥

Redis Connection: {redis_status}
Active Session: {session_status}
Live State: {state_status}
Vision Stream: {vision_status}
Command Queue: {queue_status}

📊 Current State Summary:
{emacs_vision.get_live_state() if state else '❌ No state available'}

🎯 System Status: {'🟢 OPERATIONAL' if all(['✅' in s for s in [redis_status, session_status, state_status]]) else '🔴 ISSUES DETECTED'}"""


if __name__ == "__main__":
    import sys

    # FastMCP runs stdio by default, no special stdio mode needed
    print("🚀 Starting Emacs Persistent Vision MCP Server...", file=sys.stderr)
    print("Available tools:", file=sys.stderr)
    print("  - get_emacs_state: Get real-time Emacs state", file=sys.stderr)
    print("  - execute_elisp: Execute Elisp code", file=sys.stderr)
    print("  - switch_buffer: Switch to a buffer", file=sys.stderr)
    print("  - create_buffer_with_content: Create buffer with content", file=sys.stderr)
    print("  - split_window: Split windows", file=sys.stderr)
    print("  - goto_line: Move cursor to line", file=sys.stderr)
    print("  - insert_text: Insert text at cursor", file=sys.stderr)
    print("  - get_vision_history: See recent changes", file=sys.stderr)
    print("  - emacs_health_check: System health report", file=sys.stderr)
    print("👁️ Persistent vision enabled!", file=sys.stderr)

    # FastMCP.run() handles stdio automatically
    mcp.run()
