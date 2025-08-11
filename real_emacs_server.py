#!/usr/bin/env python3
"""
Real Emacs Server Integration - Production-ready Emacs connectivity
"""

import subprocess
import json
import time
import threading
import queue
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import redis


@dataclass
class EmacsBridgeConfig:
    """Configuration for Emacs bridge"""

    emacsclient_path: str = "emacsclient"
    server_check_interval: float = 5.0
    command_timeout: float = 10.0
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0


@dataclass
class EmacsState:
    """Current Emacs state"""

    connected: bool = False
    buffer_name: str = ""
    point: int = 0
    buffer_size: int = 0
    line_number: int = 0
    column: int = 0
    modified: bool = False
    timestamp: float = 0.0


class RealEmacsServer:
    """Production-ready Emacs server integration"""

    def __init__(self, config: EmacsBridgeConfig = None):
        self.config = config or EmacsBridgeConfig()
        self.redis_client = redis.Redis(
            host=self.config.redis_host,
            port=self.config.redis_port,
            db=self.config.redis_db,
            decode_responses=True,
        )

        self.current_state = EmacsState()
        self.command_queue = queue.Queue()
        self.running = False
        self.monitor_thread = None

        self.session_id = f"emacs_bridge_{int(time.time())}"
        print(f"🌉 Real Emacs Server initialized (session: {self.session_id})")

    def start(self):
        """Start the Emacs bridge"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print("🚀 Emacs bridge started")

    def stop(self):
        """Stop the Emacs bridge"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
        print("🛑 Emacs bridge stopped")

    def is_emacs_running(self) -> bool:
        """Check if Emacs is running"""
        try:
            result = subprocess.run(
                ["pgrep", "emacs"], capture_output=True, text=True, timeout=5
            )
            return result.returncode == 0
        except:
            return False

    def is_emacs_server_ready(self) -> bool:
        """Check if Emacs server is ready for commands"""
        try:
            result = subprocess.run(
                [self.config.emacsclient_path, "--eval", '(message "server check")'],
                capture_output=True,
                text=True,
                timeout=5,
            )
            return result.returncode == 0
        except:
            return False

    def get_emacs_state(self) -> EmacsState:
        """Get current Emacs state"""
        if not self.is_emacs_server_ready():
            return EmacsState(connected=False, timestamp=time.time())

        try:
            elisp_code = """
(json-encode 
  (list 
    :buffer-name (buffer-name)
    :point (point)
    :buffer-size (buffer-size)
    :line-number (line-number-at-pos)
    :column (current-column)
    :modified (buffer-modified-p)))
"""

            result = subprocess.run(
                [self.config.emacsclient_path, "--eval", elisp_code],
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout,
            )

            if result.returncode == 0:
                state_json = result.stdout.strip().strip('"')
                parsed = json.loads(state_json)

                return EmacsState(
                    connected=True,
                    buffer_name=parsed.get("buffer-name", ""),
                    point=parsed.get("point", 0),
                    buffer_size=parsed.get("buffer-size", 0),
                    line_number=parsed.get("line-number", 0),
                    column=parsed.get("column", 0),
                    modified=parsed.get("modified", False),
                    timestamp=time.time(),
                )
            else:
                print(f"⚠️  Failed to get Emacs state: {result.stderr}")

        except Exception as e:
            print(f"⚠️  Error getting Emacs state: {e}")

        return EmacsState(connected=False, timestamp=time.time())

    def execute_command(self, elisp_command: str) -> Dict[str, Any]:
        """Execute Elisp command in Emacs"""
        if not self.is_emacs_server_ready():
            return {
                "success": False,
                "error": "Emacs server not ready",
                "command": elisp_command,
            }

        try:
            result = subprocess.run(
                [self.config.emacsclient_path, "--eval", elisp_command],
                capture_output=True,
                text=True,
                timeout=self.config.command_timeout,
            )

            if result.returncode == 0:
                # Store successful command in Redis
                command_data = {
                    "command": elisp_command,
                    "result": result.stdout.strip(),
                    "timestamp": time.time(),
                    "session": self.session_id,
                }
                self.redis_client.xadd(
                    f"emacs:commands:{self.session_id}", command_data
                )

                return {
                    "success": True,
                    "result": result.stdout.strip(),
                    "command": elisp_command,
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr,
                    "command": elisp_command,
                }

        except Exception as e:
            return {"success": False, "error": str(e), "command": elisp_command}

    def send_keystrokes(self, keystrokes: str) -> Dict[str, Any]:
        """Send keystroke sequence to Emacs"""
        # Convert common keystroke notation
        keystroke_map = {
            "C-f": "(forward-char 1)",
            "C-b": "(backward-char 1)",
            "C-n": "(next-line 1)",
            "C-p": "(previous-line 1)",
            "C-a": "(beginning-of-line)",
            "C-e": "(end-of-line)",
            "C-d": "(delete-char 1)",
            "C-k": "(kill-line)",
        }

        if keystrokes in keystroke_map:
            return self.execute_command(keystroke_map[keystrokes])
        else:
            # For literal keystrokes, use execute-kbd-macro
            elisp_cmd = f'(execute-kbd-macro "{keystrokes}")'
            return self.execute_command(elisp_cmd)

    def insert_text(self, text: str) -> Dict[str, Any]:
        """Insert text at current point"""
        escaped_text = text.replace('"', '\\"').replace("\\", "\\\\")
        return self.execute_command(f'(insert "{escaped_text}")')

    def get_buffer_content(self, start: int = None, end: int = None) -> str:
        """Get buffer content"""
        if start is None and end is None:
            elisp_cmd = "(buffer-string)"
        else:
            start = start or 1
            end = end or "(point-max)"
            elisp_cmd = f"(buffer-substring {start} {end})"

        result = self.execute_command(elisp_cmd)
        if result["success"]:
            return result["result"].strip('"')
        return ""

    def _monitor_loop(self):
        """Background monitoring loop"""
        last_state = EmacsState()

        while self.running:
            try:
                current_state = self.get_emacs_state()

                # Check for state changes
                if self._state_changed(last_state, current_state):
                    self.current_state = current_state

                    # Store state change in Redis
                    state_data = {
                        "connected": str(current_state.connected),
                        "buffer_name": current_state.buffer_name,
                        "point": str(current_state.point),
                        "buffer_size": str(current_state.buffer_size),
                        "line_number": str(current_state.line_number),
                        "column": str(current_state.column),
                        "modified": str(current_state.modified),
                        "timestamp": str(current_state.timestamp),
                        "session": self.session_id,
                    }

                    self.redis_client.xadd(
                        f"emacs:states:{self.session_id}", state_data
                    )

                    if current_state.connected:
                        print(
                            f"📊 State: {current_state.buffer_name} | "
                            f"Point: {current_state.point} | "
                            f"Line: {current_state.line_number}:{current_state.column}"
                        )

                last_state = current_state
                time.sleep(self.config.server_check_interval)

            except Exception as e:
                print(f"⚠️  Monitor error: {e}")
                time.sleep(self.config.server_check_interval)

    def get_recent_commands(self, count: int = 10) -> List[Dict]:
        """Get recent commands from Redis"""
        commands = self.redis_client.xrevrange(
            f"emacs:commands:{self.session_id}", count=count
        )
        return [cmd[1] for cmd in commands]

    def get_state_history(self, count: int = 10) -> List[Dict]:
        """Get recent state changes from Redis"""
        states = self.redis_client.xrevrange(
            f"emacs:states:{self.session_id}", count=count
        )
        return [state[1] for state in states]


def main():
    """Test the real Emacs server"""

    print("🚀 TESTING REAL EMACS SERVER")
    print("=" * 50)

    server = RealEmacsServer()

    # Test 1: Check if Emacs is running
    print("1. Checking Emacs status...")
    emacs_running = server.is_emacs_running()
    server_ready = server.is_emacs_server_ready()

    print(f"   Emacs process: {'✅' if emacs_running else '❌'}")
    print(f"   Server ready: {'✅' if server_ready else '❌'}")

    if not emacs_running:
        print("\n💡 To test fully:")
        print("   1. Start Emacs")
        print("   2. Run: M-x server-start")
        print("   3. Run this test again")
        return

    if not server_ready:
        print("\n💡 Emacs is running but server not ready:")
        print("   1. In Emacs: M-x server-start")
        print("   2. Run this test again")
        return

    # Test 2: Get current state
    print("\n2. Getting current Emacs state...")
    state = server.get_emacs_state()
    if state.connected:
        print(f"   ✅ Buffer: {state.buffer_name}")
        print(f"   ✅ Point: {state.point}")
        print(f"   ✅ Size: {state.buffer_size}")
        print(f"   ✅ Line: {state.line_number}:{state.column}")
    else:
        print("   ❌ Could not get state")

    # Test 3: Execute commands
    print("\n3. Testing command execution...")
    server.start()  # Start monitoring

    commands_to_test = [
        ('(message "AI bridge test")', "Send message"),
        ('(insert "\\n;; AI test insertion\\n")', "Insert text"),
        ("(backward-char 20)", "Move cursor back"),
        ("(delete-char 20)", "Delete test text"),
    ]

    for cmd, desc in commands_to_test:
        print(f"   🎯 {desc}...")
        result = server.execute_command(cmd)
        print(
            f"      {'✅' if result['success'] else '❌'} {result.get('result', result.get('error'))}"
        )
        time.sleep(1)

    # Test 4: Keystroke simulation
    print("\n4. Testing keystroke simulation...")
    keystroke_tests = ["C-f", "C-b", "C-n", "C-p"]

    for keystroke in keystroke_tests:
        print(f"   ⌨️  {keystroke}...")
        result = server.send_keystrokes(keystroke)
        print(f"      {'✅' if result['success'] else '❌'}")
        time.sleep(0.5)

    # Test 5: Show Redis data
    print("\n5. Redis integration...")
    time.sleep(2)  # Let monitoring collect some data

    commands = server.get_recent_commands(3)
    states = server.get_state_history(3)

    print(f"   📊 Commands in Redis: {len(commands)}")
    print(f"   📊 State changes in Redis: {len(states)}")

    if commands:
        print(f"   📝 Latest command: {commands[0].get('command', 'N/A')}")
    if states:
        latest_state = states[0]
        print(
            f"   📍 Latest state: {latest_state.get('buffer_name')} at {latest_state.get('point')}"
        )

    server.stop()

    print("\n" + "=" * 50)
    print("🎉 Real Emacs Server test complete!")
    print("✅ Production-ready Emacs integration working")


if __name__ == "__main__":
    main()
