#!/usr/bin/env python3
"""Simple Redis command processor for Emacs"""

import redis
import subprocess
import time
import json


def main():
    r = redis.Redis(decode_responses=True)
    print("🚀 Simple command processor started")

    while True:
        try:
            # Poll for commands every 2 seconds
            command = r.lpop("emacs:commands")
            if command:
                print(f"📋 Executing: {command}")

                # Execute via emacsclient 
                result = subprocess.run(
                    ["emacsclient", "-s", "claude", "--eval", command],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    print(f"✅ Success: {result.stdout.strip()}")
                    r.set("emacs:last_command_result", result.stdout.strip())
                    # Store state info in Redis
                    if "buffer" in command.lower() or "point" in command.lower():
                        r.hset("emacs:state", "last_query", result.stdout.strip())
                else:
                    print(f"❌ Error: {result.stderr}")
                    r.set("emacs:last_command_result", f"error: {result.stderr}")

            time.sleep(2)

        except KeyboardInterrupt:
            print("🛑 Stopping command processor")
            break
        except Exception as e:
            print(f"⚠️ Error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
