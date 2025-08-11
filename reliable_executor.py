#!/usr/bin/env python3
"""
Reliable Redis → Emacs Executor
Forces command execution using direct emacsclient calls
"""
import redis
import subprocess
import time
import json


class ReliableExecutor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.last_id = "0"

    def start_executing(self):
        """Start executing commands from Redis streams"""
        print("🔧 RELIABLE EXECUTOR STARTED")
        print("Processing Redis commands with direct emacsclient calls...")
        print("-" * 60)

        while True:
            try:
                # Read new commands from stream
                result = self.redis_client.xread(
                    {"emacs:nlp-commands": self.last_id}, count=1, block=1000
                )

                if result:
                    stream_name, messages = result[0]
                    for message_id, fields in messages:
                        self.execute_command(message_id, fields)
                        self.last_id = message_id

            except KeyboardInterrupt:
                print("\n⏹️ Executor stopped")
                break
            except Exception as e:
                print(f"❌ Executor error: {e}")
                time.sleep(1)

    def execute_command(self, message_id, fields):
        """Execute a single command with direct emacsclient"""
        step = fields.get("step", "?")
        elisp = fields.get("elisp", "")
        description = fields.get("description", "")

        print(f"🚀 STEP {step}: {description}")
        print(f"   Elisp: {elisp}")

        if not elisp:
            print("   ❌ No elisp code to execute")
            return

        try:
            # Direct emacsclient execution
            result = subprocess.run(
                ["emacsclient", "--eval", elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                print(f"   ✅ SUCCESS: {result.stdout.strip()}")

                # Log success to Redis
                self.redis_client.xadd(
                    "emacs:execution-log",
                    {
                        "step": step,
                        "status": "success",
                        "result": result.stdout.strip(),
                        "timestamp": str(time.time()),
                    },
                )
            else:
                print(f"   ❌ FAILED: {result.stderr.strip()}")

                # Log failure to Redis
                self.redis_client.xadd(
                    "emacs:execution-log",
                    {
                        "step": step,
                        "status": "failed",
                        "error": result.stderr.strip(),
                        "timestamp": str(time.time()),
                    },
                )

        except subprocess.TimeoutExpired:
            print("   ⏰ TIMEOUT: Command took too long")
        except Exception as e:
            print(f"   💥 ERROR: {e}")

        print()
        time.sleep(0.5)  # Brief pause between commands


if __name__ == "__main__":
    executor = ReliableExecutor()
    executor.start_executing()
