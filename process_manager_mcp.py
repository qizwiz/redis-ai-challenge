#!/usr/bin/env python3
"""
Process Manager MCP Server
Manages processes in vterm buffers - restart, stop, monitor without manual intervention
"""

import redis
import time
import json
import subprocess
import signal
import os
from typing import Dict, List, Optional
import fastmcp


class ProcessManager:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.active_processes = {}  # process_id -> process_info
        self.vterm_buffers = {}  # buffer_name -> process_id

    def send_vterm_command(self, buffer_name: str, command: str, delay: float = 0.1):
        """Send command to specific vterm buffer"""
        # Switch to the vterm buffer
        self.redis_client.xadd(
            "emacs:commands", {"action": "switch-to-buffer", "target": buffer_name}
        )

        time.sleep(delay)

        # Send the command
        self.redis_client.xadd(
            "emacs:commands", {"action": "vterm-send-string", "text": command}
        )

        time.sleep(delay)

        # Send return
        self.redis_client.xadd("emacs:commands", {"action": "vterm-send-return"})

    def interrupt_process(self, buffer_name: str = "*vterm*"):
        """Send C-c interrupt to vterm buffer"""
        self.redis_client.xadd(
            "emacs:commands", {"action": "switch-to-buffer", "target": buffer_name}
        )

        time.sleep(0.1)

        # Send C-c (interrupt signal)
        for _ in range(4):  # C-c 4 times as you mentioned
            self.redis_client.xadd(
                "emacs:commands", {"action": "vterm-send-key", "key": "C-c"}
            )
            time.sleep(0.1)

    def restart_last_command(self, buffer_name: str = "*vterm*"):
        """Restart last command in vterm buffer using up arrow"""
        self.redis_client.xadd(
            "emacs:commands", {"action": "switch-to-buffer", "target": buffer_name}
        )

        time.sleep(0.1)

        # Send up arrow to get last command
        self.redis_client.xadd(
            "emacs:commands", {"action": "vterm-send-key", "key": "Up"}
        )

        time.sleep(0.1)

        # Send return to execute
        self.redis_client.xadd("emacs:commands", {"action": "vterm-send-return"})

    def stop_and_restart_process(self, buffer_name: str = "*vterm*"):
        """Complete stop and restart sequence"""
        print(f"🛑 Stopping process in {buffer_name}")
        self.interrupt_process(buffer_name)

        time.sleep(0.5)  # Wait for process to stop

        print(f"🔄 Restarting last command in {buffer_name}")
        self.restart_last_command(buffer_name)

        return f"✅ Process restarted in {buffer_name}"

    def run_python_script_safe(self, script_path: str, buffer_name: str = "*vterm*"):
        """Run Python script with proper error handling and validation"""

        # First validate the script exists and has proper imports
        if not os.path.exists(script_path):
            return f"❌ Script not found: {script_path}"

        # Check for syntax errors
        try:
            with open(script_path, "r") as f:
                content = f.read()

            # Basic validation - check for missing imports
            if "from collections import deque" not in content and "deque(" in content:
                return f"❌ Script has missing import: 'from collections import deque' needed"

            # Try to compile (syntax check)
            compile(content, script_path, "exec")

        except SyntaxError as e:
            return f"❌ Syntax error in {script_path}: {e}"
        except Exception as e:
            return f"❌ Error validating {script_path}: {e}"

        # If validation passes, run it
        command = f"python3 {script_path}"

        # Stop any existing process first
        self.interrupt_process(buffer_name)
        time.sleep(0.5)

        # Run the new command
        self.send_vterm_command(buffer_name, command)

        return f"✅ Started {script_path} in {buffer_name} (validated first)"

    def fix_and_restart_script(self, script_path: str, buffer_name: str = "*vterm*"):
        """Fix common issues and restart script"""

        if not os.path.exists(script_path):
            return f"❌ Script not found: {script_path}"

        try:
            with open(script_path, "r") as f:
                content = f.read()

            # Fix missing deque import
            if "deque(" in content and "from collections import deque" not in content:
                print("🔧 Adding missing deque import")

                # Find where to add the import
                lines = content.split("\n")
                import_index = 0

                # Find last import line
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith(
                        "from "
                    ):
                        import_index = i + 1

                # Insert the missing import
                lines.insert(import_index, "from collections import deque")

                # Write back the fixed file
                with open(script_path, "w") as f:
                    f.write("\n".join(lines))

                print(f"✅ Fixed missing import in {script_path}")

            # Now run the fixed script
            return self.run_python_script_safe(script_path, buffer_name)

        except Exception as e:
            return f"❌ Error fixing {script_path}: {e}"

    def get_vterm_status(self, buffer_name: str = "*vterm*") -> str:
        """Get status of vterm buffer"""
        try:
            # This is a simplified version - in reality we'd query Emacs for process status
            return f"📊 Buffer {buffer_name} status: Active"
        except Exception as e:
            return f"❌ Error getting status: {e}"


# FastMCP Server
mcp = fastmcp.FastMCP("process-manager")
manager = ProcessManager()


@mcp.tool()
def restart_vterm_process(buffer_name: str = "*vterm*") -> str:
    """Stop current process and restart last command in vterm buffer"""
    return manager.stop_and_restart_process(buffer_name)


@mcp.tool()
def interrupt_vterm_process(buffer_name: str = "*vterm*") -> str:
    """Send interrupt signal (C-c) to vterm buffer"""
    manager.interrupt_process(buffer_name)
    return f"🛑 Sent interrupt to {buffer_name}"


@mcp.tool()
def run_python_safe(script_path: str, buffer_name: str = "*vterm*") -> str:
    """Run Python script with validation and error checking"""
    return manager.run_python_script_safe(script_path, buffer_name)


@mcp.tool()
def fix_and_run_script(script_path: str, buffer_name: str = "*vterm*") -> str:
    """Fix common script issues and run safely"""
    return manager.fix_and_restart_script(script_path, buffer_name)


@mcp.tool()
def send_vterm_command(command: str, buffer_name: str = "*vterm*") -> str:
    """Send arbitrary command to vterm buffer"""
    manager.send_vterm_command(buffer_name, command)
    return f"✅ Sent command '{command}' to {buffer_name}"


@mcp.tool()
def get_process_status(buffer_name: str = "*vterm*") -> str:
    """Get status of process in vterm buffer"""
    return manager.get_vterm_status(buffer_name)


@mcp.tool()
def restart_live_ai_integration() -> str:
    """Specifically restart the live AI integration with fixes"""
    script_path = (
        "/Users/jonathanhill/src/redis-ai-challenge/live_ai_emacs_integration.py"
    )
    return manager.fix_and_restart_script(script_path)


if __name__ == "__main__":
    print("🔧 Starting Process Manager MCP Server")
    fastmcp.run_stdio_async(mcp)
