#!/usr/bin/env python3
"""
Simple Claude Bridge - Connects Emacs REPL to Claude command
"""

import redis
import subprocess
import time
import json


def process_messages():
    """Process messages from Redis and send to Claude"""

    redis_client = redis.Redis(decode_responses=True)

    print("🌉 Simple Claude Bridge Starting")
    print("📡 Monitoring Redis for messages...")

    while True:
        try:
            # Check for messages in claude:messages stream
            messages = redis_client.xrange("claude:messages", count=10)

            for message_id, fields in messages:
                message_text = fields.get("message", "")
                user = fields.get("user", "unknown")

                if message_text:
                    print(f"📨 Message from {user}: {message_text}")

                    # Send to Claude and get response
                    print("🤖 Sending to Claude...")
                    try:
                        result = subprocess.run(
                            ["/Users/jonathanhill/.bun/bin/claude", "--print"],
                            input=message_text,
                            capture_output=True,
                            text=True,
                            timeout=30,
                        )

                        if result.returncode == 0:
                            response = result.stdout.strip()
                            print(f"✅ Got response: {response[:100]}...")

                            # Store response in Redis
                            redis_client.xadd(
                                "claude:responses",
                                {
                                    "response": response,
                                    "timestamp": time.time(),
                                    "message_id": message_id,
                                },
                            )

                            print("💾 Response stored in Redis")

                        else:
                            error_msg = result.stderr.strip()
                            print(f"❌ Error: {error_msg}")

                            redis_client.xadd(
                                "claude:responses",
                                {
                                    "response": f"Error: {error_msg}",
                                    "timestamp": time.time(),
                                    "message_id": message_id,
                                },
                            )

                    except Exception as e:
                        print(f"💥 Exception: {e}")
                        redis_client.xadd(
                            "claude:responses",
                            {
                                "response": f"Bridge error: {str(e)}",
                                "timestamp": time.time(),
                                "message_id": message_id,
                            },
                        )

                    # Remove processed message
                    redis_client.xdel("claude:messages", message_id)

            time.sleep(2)  # Check every 2 seconds

        except KeyboardInterrupt:
            print("\n🛑 Bridge stopped")
            break
        except Exception as e:
            print(f"💥 Bridge error: {e}")
            time.sleep(5)


if __name__ == "__main__":
    process_messages()
