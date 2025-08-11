#!/usr/bin/env python3
"""
Claude Status Monitor - Background Server
Monitors Claude activity and updates Emacs titlebar via Redis
"""

import redis
import time
import subprocess
import json
import threading
from datetime import datetime


class ClaudeStatusMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.running = True
        self.last_claude_activity = 0

    def is_claude_actually_busy(self):
        """Detect if Claude is actually processing something"""
        try:
            # Check for active Claude Code processes with high CPU
            result = subprocess.run(
                ["ps", "aux"], capture_output=True, text=True, timeout=2
            )

            lines = result.stdout.split("\n")
            active_claude = False

            for line in lines:
                if "claude" in line.lower() or "anthropic" in line.lower():
                    parts = line.split()
                    if len(parts) >= 3:
                        try:
                            cpu_percent = float(parts[2])
                            if cpu_percent > 1.0:  # More than 1% CPU = actually working
                                active_claude = True
                                break
                        except:
                            continue

            return active_claude

        except:
            return False

    def check_redis_command_activity(self):
        """Check for recent command activity in Redis"""
        try:
            # Check last command timestamp
            recent = self.redis_client.xrevrange("emacs:commands", count=1)
            if recent:
                cmd_id = recent[0][0]
                timestamp_ms = int(cmd_id.split("-")[0])
                timestamp_s = timestamp_ms / 1000

                # If command was in last 10 seconds, consider active
                if time.time() - timestamp_s < 10:
                    return True

            return False
        except:
            return False

    def determine_claude_status(self):
        """Determine current Claude status"""
        current_time = time.time()

        # Check actual activity
        process_busy = self.is_claude_actually_busy()
        redis_active = self.check_redis_command_activity()

        if process_busy or redis_active:
            self.last_claude_activity = current_time

        # Determine status based on time since last activity
        time_since_activity = current_time - self.last_claude_activity

        if time_since_activity < 5:
            return "🔴 CLAUDE BUSY"
        elif time_since_activity < 30:
            return "🟡 CLAUDE FINISHING"
        else:
            return "🟢 CLAUDE READY"

    def update_emacs_titlebar(self, status):
        """Update Emacs titlebar via emacsclient"""
        try:
            title = f"Emacs - {status}"
            subprocess.run(
                [
                    "emacsclient",
                    "--eval",
                    f'(modify-frame-parameters nil \'((title . "{title}")))',
                ],
                timeout=1,
                capture_output=True,
            )

            # Also store in Redis for other tools
            self.redis_client.set("claude:status", status)
            self.redis_client.set("claude:last_update", time.time())

        except Exception as e:
            print(f"Error updating titlebar: {e}")

    def run_server(self):
        """Main server loop"""
        print("🚀 Claude Status Monitor Server Started")
        print("   • Monitoring actual Claude process activity")
        print("   • Updating Emacs titlebar every 3 seconds")
        print("   • Running as background daemon")

        while self.running:
            try:
                status = self.determine_claude_status()
                self.update_emacs_titlebar(status)

                # Log status changes
                current_hour_min = datetime.now().strftime("%H:%M")
                print(f"[{current_hour_min}] {status}")

                time.sleep(3)  # Update every 3 seconds

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Monitor error: {e}")
                time.sleep(5)

        print("⏹️ Claude Status Monitor stopped")


def main():
    monitor = ClaudeStatusMonitor()
    monitor.run_server()


if __name__ == "__main__":
    main()
