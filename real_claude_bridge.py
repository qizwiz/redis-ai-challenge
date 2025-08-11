#!/usr/bin/env python3
"""
Real Claude Bridge - Connects Redis streams to actual Claude API
No fake responses - real bidirectional conversation
"""

import redis
import time
import os
import json
from anthropic import Anthropic


class RealClaudeBridge:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)

        # Initialize Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable required")

        self.anthropic = Anthropic(api_key=api_key)
        self.processed_messages = set()

        print("🌐 Real Claude Bridge Starting")
        print("📡 Connected to Redis and Anthropic API")

    def run(self):
        """Main loop - monitor Redis for messages, send to real Claude, return responses"""

        while True:
            try:
                # Get messages from Redis stream
                messages = self.redis_client.xrange("claude:messages", count=10)

                for message_id, fields in messages:
                    if message_id in self.processed_messages:
                        continue

                    user_message = fields.get("message", "")
                    user = fields.get("user", "unknown")

                    if user_message:
                        print(f"📨 User message: {user_message}")

                        # Send to real Claude API
                        try:
                            response = self.anthropic.messages.create(
                                model="claude-3-5-sonnet-20241022",
                                max_tokens=1000,
                                messages=[{"role": "user", "content": user_message}],
                            )

                            claude_response = response.content[0].text

                            print(f"🤖 Claude response: {claude_response[:100]}...")

                            # Send real response back to Redis
                            self.redis_client.xadd(
                                "claude:responses",
                                {
                                    "response": claude_response,
                                    "timestamp": time.time(),
                                    "from": "real-claude-api",
                                    "in_reply_to": user_message,
                                    "message_id": message_id,
                                },
                            )

                            print("✅ Real response sent to Emacs via Redis")

                        except Exception as e:
                            error_response = f"Error connecting to Claude API: {str(e)}"
                            print(f"❌ API Error: {e}")

                            self.redis_client.xadd(
                                "claude:responses",
                                {
                                    "response": error_response,
                                    "timestamp": time.time(),
                                    "from": "claude-bridge-error",
                                    "error": str(e),
                                },
                            )

                        self.processed_messages.add(message_id)

                time.sleep(1)  # Check every second

            except KeyboardInterrupt:
                print("\n👋 Real Claude Bridge stopped")
                break
            except Exception as e:
                print(f"💥 Bridge Error: {e}")
                time.sleep(2)


def main():
    """Start the real Claude bridge"""

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("❌ ANTHROPIC_API_KEY environment variable required")
        print("   Set it with: export ANTHROPIC_API_KEY=your_key_here")
        return

    try:
        bridge = RealClaudeBridge()
        bridge.run()
    except Exception as e:
        print(f"❌ Failed to start bridge: {e}")


if __name__ == "__main__":
    main()
