#!/usr/bin/env python3
"""
Reactive Facade Server
Continuously monitors ALL Emacs changes (user + AI) and maintains live state
"""

import redis
import subprocess
import json
import time
import threading
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
import hashlib


@dataclass
class EmacsState:
    """Complete Emacs state snapshot"""

    timestamp: float
    window_count: int
    window_layout: str
    current_buffer: str
    buffer_list: list
    cursor_position: int
    cursor_line: int
    cursor_column: int
    major_mode: str
    minor_modes: list
    buffer_contents_hash: str
    last_command: Optional[str] = None
    change_source: str = "unknown"


class ReactiveFacadeServer:
    def __init__(self, poll_interval: float = 0.1):
        self.redis_client = redis.Redis(decode_responses=True)
        self.poll_interval = poll_interval
        self.running = True
        self.last_state = None
        self.change_counter = 0

        # Event streams
        self.state_stream = "emacs:state_events"
        self.change_stream = "emacs:change_events"
        self.facade_key = "emacs:live_facade"

    def get_emacs_state(self) -> Optional[EmacsState]:
        """Get comprehensive current Emacs state"""
        try:
            # Get all state in one batch for consistency
            commands = [
                "(length (window-list))",
                '(if (> (length (window-list)) 1) "split" "single")',
                "(buffer-name)",
                "(mapcar 'buffer-name (buffer-list))",
                "(point)",
                "(line-number-at-pos)",
                "(current-column)",
                "(symbol-name major-mode)",
                "(mapcar 'symbol-name minor-mode-list)",
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

            # Parse results
            window_count = int(results[0])
            window_layout = results[1].strip('"')
            current_buffer = results[2].strip('"')

            # Parse buffer list (comes as elisp list)
            buffer_list_raw = results[3].strip("()")
            buffer_list = [
                b.strip('"') for b in buffer_list_raw.split('" "') if b.strip()
            ]

            cursor_position = int(results[4])
            cursor_line = int(results[5])
            cursor_column = int(results[6])
            major_mode = results[7].strip('"')

            # Parse minor modes
            minor_modes_raw = results[8].strip("()")
            minor_modes = (
                [m.strip('" ') for m in minor_modes_raw.split() if m.strip()]
                if minor_modes_raw
                else []
            )

            # Hash buffer contents for change detection
            buffer_contents = results[9].strip('"')
            contents_hash = hashlib.md5(buffer_contents.encode()).hexdigest()

            return EmacsState(
                timestamp=time.time(),
                window_count=window_count,
                window_layout=window_layout,
                current_buffer=current_buffer,
                buffer_list=buffer_list,
                cursor_position=cursor_position,
                cursor_line=cursor_line,
                cursor_column=cursor_column,
                major_mode=major_mode,
                minor_modes=minor_modes,
                buffer_contents_hash=contents_hash,
            )

        except Exception as e:
            print(f"Error getting Emacs state: {e}")
            return None

    def detect_changes(self, old_state: EmacsState, new_state: EmacsState) -> list:
        """Detect what changed between states"""
        changes = []

        if old_state.window_count != new_state.window_count:
            changes.append(
                {
                    "type": "window_count_change",
                    "from": old_state.window_count,
                    "to": new_state.window_count,
                    "action": (
                        "split"
                        if new_state.window_count > old_state.window_count
                        else "merge"
                    ),
                }
            )

        if old_state.window_layout != new_state.window_layout:
            changes.append(
                {
                    "type": "window_layout_change",
                    "from": old_state.window_layout,
                    "to": new_state.window_layout,
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
                    "type": "buffer_content_change",
                    "buffer": new_state.current_buffer,
                    "cursor_moved": old_state.cursor_position
                    != new_state.cursor_position,
                }
            )

        if old_state.cursor_position != new_state.cursor_position:
            changes.append(
                {
                    "type": "cursor_movement",
                    "from": old_state.cursor_position,
                    "to": new_state.cursor_position,
                    "line_change": old_state.cursor_line != new_state.cursor_line,
                }
            )

        return changes

    def determine_change_source(self, changes: list) -> str:
        """Determine if changes came from user or AI commands"""
        # Check if we have recent Redis commands that match these changes
        try:
            recent_commands = self.redis_client.xrevrange("emacs:commands", count=5)
            if recent_commands:
                # If we have recent commands within last 2 seconds, likely AI-driven
                latest_cmd_time = int(recent_commands[0][0].split("-")[0]) / 1000
                if time.time() - latest_cmd_time < 2.0:
                    return "ai_command"

            # Otherwise, likely user-driven
            return "user_action"
        except:
            return "unknown"

    def publish_changes(self, changes: list, new_state: EmacsState):
        """Publish detected changes to Redis streams"""
        change_source = self.determine_change_source(changes)
        new_state.change_source = change_source

        # Publish each change as individual event
        for change in changes:
            change_event = {
                "change_id": f"{self.change_counter}",
                "timestamp": new_state.timestamp,
                "source": change_source,
                "change_type": change["type"],
                "change_data": json.dumps(change),
                "state_snapshot": json.dumps(asdict(new_state)),
            }

            self.redis_client.xadd(self.change_stream, change_event)
            self.change_counter += 1

        # Update live facade
        self.redis_client.set(self.facade_key, json.dumps(asdict(new_state)))

        # Publish state update
        self.redis_client.xadd(
            self.state_stream,
            {
                "timestamp": new_state.timestamp,
                "window_count": new_state.window_count,
                "current_buffer": new_state.current_buffer,
                "change_source": change_source,
                "changes_count": len(changes),
            },
        )

        print(f"🔔 Detected {len(changes)} changes from {change_source}:")
        for change in changes:
            print(f"   • {change['type']}: {change}")

    def monitor_loop(self):
        """Main monitoring loop"""
        print("🎯 **REACTIVE FACADE SERVER STARTED**")
        print(f"   Polling interval: {self.poll_interval}s")
        print(f"   Monitoring streams: {self.change_stream}, {self.state_stream}")
        print("   Watching for ALL Emacs changes (user + AI)...")

        while self.running:
            try:
                current_state = self.get_emacs_state()

                if current_state:
                    if self.last_state:
                        changes = self.detect_changes(self.last_state, current_state)
                        if changes:
                            self.publish_changes(changes, current_state)

                    self.last_state = current_state

                time.sleep(self.poll_interval)

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(1)

        print("⏹️ Reactive Facade Server stopped")

    def start_server(self):
        """Start the reactive facade server"""
        monitor_thread = threading.Thread(target=self.monitor_loop, daemon=True)
        monitor_thread.start()
        return monitor_thread

    def get_current_facade(self) -> Optional[dict]:
        """Get current facade state"""
        try:
            facade_json = self.redis_client.get(self.facade_key)
            return json.loads(facade_json) if facade_json else None
        except:
            return None

    def get_recent_changes(self, count: int = 10) -> list:
        """Get recent change events"""
        try:
            changes = self.redis_client.xrevrange(self.change_stream, count=count)
            return [{"id": change_id, "data": fields} for change_id, fields in changes]
        except:
            return []


def main():
    """Run reactive facade server"""
    server = ReactiveFacadeServer(poll_interval=0.2)  # 5 times per second

    try:
        server.monitor_loop()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")


if __name__ == "__main__":
    main()
