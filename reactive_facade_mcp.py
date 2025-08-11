#!/usr/bin/env python3
"""
Reactive Facade MCP Server
Monitors ALL Emacs changes and provides intelligent responses via headless Claude
"""

import fastmcp
import redis
import subprocess
import json
import time
import threading
import asyncio
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class EmacsState:
    timestamp: float
    window_count: int
    window_layout: str
    current_buffer: str
    cursor_position: int
    cursor_line: int
    cursor_column: int
    buffer_contents_hash: str
    change_source: str = "unknown"


class ReactiveFacadeMCP:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.last_state = None
        self.running = True
        self.change_counter = 0

        # Start monitoring in background thread
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def get_emacs_state(self) -> Optional[EmacsState]:
        """Get current Emacs state"""
        try:
            commands = [
                "(length (window-list))",
                '(if (> (length (window-list)) 1) "split" "single")',
                "(buffer-name)",
                "(point)",
                "(line-number-at-pos)",
                "(current-column)",
                "(buffer-string)",
            ]

            results = []
            for cmd in commands:
                result = subprocess.run(
                    ["emacsclient", "--eval", cmd],
                    capture_output=True,
                    text=True,
                    timeout=1,
                )
                results.append(result.stdout.strip())

            window_count = int(results[0])
            window_layout = results[1].strip('"')
            current_buffer = results[2].strip('"')
            cursor_position = int(results[3])
            cursor_line = int(results[4])
            cursor_column = int(results[5])
            buffer_contents = results[6].strip('"')
            contents_hash = hashlib.md5(buffer_contents.encode()).hexdigest()

            return EmacsState(
                timestamp=time.time(),
                window_count=window_count,
                window_layout=window_layout,
                current_buffer=current_buffer,
                cursor_position=cursor_position,
                cursor_line=cursor_line,
                cursor_column=cursor_column,
                buffer_contents_hash=contents_hash,
            )
        except Exception as e:
            print(f"Error getting state: {e}")
            return None

    def detect_changes(self, old_state: EmacsState, new_state: EmacsState) -> list:
        """Detect changes between states"""
        changes = []

        if old_state.window_count != new_state.window_count:
            changes.append(
                {
                    "type": "window_change",
                    "action": (
                        "split"
                        if new_state.window_count > old_state.window_count
                        else "merge"
                    ),
                    "from": old_state.window_count,
                    "to": new_state.window_count,
                }
            )

        if old_state.current_buffer != new_state.current_buffer:
            changes.append(
                {
                    "type": "buffer_switch",
                    "from": old_state.current_buffer,
                    "to": new_state.current_buffer,
                }
            )

        if old_state.buffer_contents_hash != new_state.buffer_contents_hash:
            changes.append(
                {
                    "type": "content_change",
                    "buffer": new_state.current_buffer,
                    "cursor_moved": old_state.cursor_position
                    != new_state.cursor_position,
                }
            )

        return changes

    def determine_change_source(self, changes: list) -> str:
        """Determine if changes are from user or AI"""
        try:
            recent_commands = self.redis_client.xrevrange("emacs:commands", count=3)
            if recent_commands:
                latest_cmd_time = int(recent_commands[0][0].split("-")[0]) / 1000
                if time.time() - latest_cmd_time < 2.0:
                    return "ai_command"
            return "user_action"
        except:
            return "unknown"

    def _intelligent_response_to_user_change(self, changes: list, state: EmacsState):
        """Trigger intelligent response to user changes via headless Claude"""
        if not changes:
            return

        # Build context about what the user did
        change_description = []
        for change in changes:
            if change["type"] == "window_change":
                if change["action"] == "split":
                    change_description.append(
                        f"User split windows (now {change['to']} windows)"
                    )
                else:
                    change_description.append(
                        f"User merged windows (now {change['to']} windows)"
                    )
            elif change["type"] == "buffer_switch":
                change_description.append(f"User switched to buffer: {change['to']}")
            elif change["type"] == "content_change":
                change_description.append(f"User edited content in {change['buffer']}")

        context = f"""
USER ACTION DETECTED:
{'; '.join(change_description)}

Current Emacs State:
- Windows: {state.window_count} ({state.window_layout})
- Buffer: {state.current_buffer}
- Cursor: Line {state.cursor_line}, Column {state.cursor_column}

Respond with a brief, helpful insight about this user action. Be encouraging and contextually aware.
"""

        try:
            # Use headless Claude to generate intelligent response
            result = subprocess.run(
                ["claude", "-p", context, "--mcp-config", ".mcp.json"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0 and result.stdout.strip():
                response = result.stdout.strip()

                # Send intelligent response to user via Emacs
                safe_response = response.replace('"', '\\"').replace("\n", "\\n")
                subprocess.run(
                    [
                        "emacsclient",
                        "--eval",
                        f'(message "🤖 AI: {safe_response[:100]}...")',
                    ],
                    timeout=2,
                )

                # Log the interaction
                self.redis_client.xadd(
                    "ai:user_interactions",
                    {
                        "timestamp": time.time(),
                        "user_action": json.dumps(changes),
                        "ai_response": response,
                        "context": f"windows:{state.window_count}, buffer:{state.current_buffer}",
                    },
                )

                print(f"🤖 AI Response to user action: {response[:50]}...")

        except Exception as e:
            print(f"Error generating AI response: {e}")

    def _monitor_loop(self):
        """Background monitoring loop"""
        print("🎯 Reactive Facade MCP: Monitoring ALL Emacs changes...")

        while self.running:
            try:
                current_state = self.get_emacs_state()

                if current_state and self.last_state:
                    changes = self.detect_changes(self.last_state, current_state)

                    if changes:
                        change_source = self.determine_change_source(changes)
                        current_state.change_source = change_source

                        # Store in Redis
                        self.redis_client.xadd(
                            "emacs:live_changes",
                            {
                                "timestamp": current_state.timestamp,
                                "changes": json.dumps(changes),
                                "source": change_source,
                                "state": json.dumps(asdict(current_state)),
                            },
                        )

                        print(
                            f"🔔 Detected {change_source}: {[c['type'] for c in changes]}"
                        )

                        # Intelligent response to USER actions only
                        if change_source == "user_action":
                            self._intelligent_response_to_user_change(
                                changes, current_state
                            )

                if current_state:
                    self.last_state = current_state

                time.sleep(0.3)  # Monitor every 300ms

            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)


# FastMCP Server
mcp = fastmcp.FastMCP("reactive-facade")
facade = ReactiveFacadeMCP()


@mcp.tool()
def get_facade_state() -> str:
    """Get current live Emacs facade state"""
    if facade.last_state:
        state = facade.last_state
        return f"""🎯 **LIVE EMACS FACADE**
Windows: {state.window_count} ({state.window_layout})
Buffer: {state.current_buffer}
Cursor: Line {state.cursor_line}, Col {state.cursor_column}
Last Update: {time.strftime('%H:%M:%S', time.localtime(state.timestamp))}
Source: {state.change_source}"""
    return "❌ No facade state available"


@mcp.tool()
def get_recent_changes(count: int = 5) -> str:
    """Get recent Emacs change events"""
    try:
        changes = facade.redis_client.xrevrange("emacs:live_changes", count=count)

        if not changes:
            return "No recent changes detected"

        result = "📊 **RECENT EMACS CHANGES**\n"
        for change_id, fields in changes:
            timestamp = float(fields.get("timestamp", 0))
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            source = fields.get("source", "unknown")
            changes_data = json.loads(fields.get("changes", "[]"))

            result += f"\n[{time_str}] {source.upper()}:\n"
            for change in changes_data:
                result += f"  • {change['type']}: {change}\n"

        return result
    except Exception as e:
        return f"Error getting changes: {e}"


@mcp.tool()
def get_user_interactions(count: int = 3) -> str:
    """Get recent AI responses to user actions"""
    try:
        interactions = facade.redis_client.xrevrange(
            "ai:user_interactions", count=count
        )

        if not interactions:
            return "No recent user interactions"

        result = "🤖 **AI RESPONSES TO USER ACTIONS**\n"
        for interaction_id, fields in interactions:
            timestamp = float(fields.get("timestamp", 0))
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            user_action = fields.get("user_action", "[]")
            ai_response = fields.get("ai_response", "")

            result += f"\n[{time_str}] User Action: {user_action}\n"
            result += f"AI Response: {ai_response[:100]}...\n"

        return result
    except Exception as e:
        return f"Error getting interactions: {e}"


@mcp.tool()
def trigger_intelligent_response(context: str) -> str:
    """Manually trigger intelligent response to current Emacs state"""
    current_state = facade.get_emacs_state()
    if not current_state:
        return "❌ Could not get current Emacs state"

    try:
        prompt = f"Current Emacs state: {current_state.window_count} windows, buffer {current_state.current_buffer}. Context: {context}. Provide helpful insight."

        result = subprocess.run(
            ["claude", "-p", prompt, "--mcp-config", ".mcp.json"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0:
            return f"🤖 AI Response: {result.stdout.strip()}"
        else:
            return f"❌ Error: {result.stderr}"
    except Exception as e:
        return f"❌ Error: {e}"


if __name__ == "__main__":
    print("🚀 Starting Reactive Facade MCP Server...")
    print("   • Monitoring ALL Emacs changes (user + AI)")
    print("   • Providing intelligent responses via headless Claude")
    print("   • Available as MCP tools for Claude Code integration")
    mcp.run()
