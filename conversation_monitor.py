#!/usr/bin/env python3
"""
Conversation Monitor - Watch Redis streams for user messages and facilitate responses
"""

import redis
import time
import json
from datetime import datetime


class ConversationMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        print("🎧 Starting conversation monitor...")
        print("📡 Connected to Redis streams")
        print("🔄 Monitoring claude:messages for user input")
        print("📤 Ready to send responses to claude:responses")
        print("-" * 60)

    def monitor_messages(self):
        """Monitor for new user messages and show them"""
        last_id = "$"  # Start from newest messages

        while True:
            try:
                # Listen for new messages
                streams = self.redis_client.xread(
                    {"claude:messages": last_id},
                    count=1,
                    block=1000,  # 1 second timeout
                )

                if streams:
                    stream_name, messages = streams[0]
                    for message_id, fields in messages:
                        self.display_user_message(message_id, fields)
                        last_id = message_id

            except KeyboardInterrupt:
                print("\n🛑 Stopping conversation monitor...")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                time.sleep(1)

    def display_user_message(self, message_id, fields):
        """Display a user message and prompt for response"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        message = fields.get("message", fields.get("content", ""))
        user = fields.get("user", "User")

        print(f"\n[{timestamp}] 📨 NEW MESSAGE from {user}:")
        print(f"Message ID: {message_id}")
        print(f"Content: {message}")
        print("-" * 60)
        print("💭 What should I respond? (Type your response or 'skip' to ignore)")
        print("Response: ", end="", flush=True)

        # Wait for user input
        try:
            response = input()
            if response.lower() != "skip" and response.strip():
                self.send_response(response, message_id, message)
        except (KeyboardInterrupt, EOFError):
            print("\n🛑 Exiting...")
            return False

        return True

    def send_response(self, response_text, original_message_id, original_message):
        """Send a response back through the Redis stream"""
        try:
            response_data = {
                "response": response_text,
                "timestamp": str(time.time()),
                "message_id": original_message_id,
                "from": "claude-conversation-monitor",
                "in_reply_to": original_message,
            }

            result = self.redis_client.xadd("claude:responses", response_data)
            print(f"✅ Response sent! ID: {result}")
            print("-" * 60)

        except Exception as e:
            print(f"❌ Failed to send response: {e}")

    def show_recent_conversation(self):
        """Show recent conversation history"""
        print("\n📜 RECENT CONVERSATION HISTORY:")
        print("=" * 60)

        # Get recent messages
        try:
            messages = self.redis_client.xrevrange("claude:messages", count=5)
            responses = self.redis_client.xrevrange("claude:responses", count=5)

            # Combine and sort by timestamp
            all_items = []

            for msg_id, fields in messages:
                all_items.append(
                    {
                        "id": msg_id,
                        "type": "message",
                        "content": fields.get("message", fields.get("content", "")),
                        "user": fields.get("user", "User"),
                        "timestamp": float(msg_id.split("-")[0]) / 1000,
                    }
                )

            for resp_id, fields in responses:
                all_items.append(
                    {
                        "id": resp_id,
                        "type": "response",
                        "content": fields.get("response", ""),
                        "from": fields.get("from", "Claude"),
                        "timestamp": float(resp_id.split("-")[0]) / 1000,
                    }
                )

            # Sort by timestamp
            all_items.sort(key=lambda x: x["timestamp"])

            for item in all_items[-10:]:  # Show last 10 items
                ts = datetime.fromtimestamp(item["timestamp"]).strftime("%H:%M:%S")
                if item["type"] == "message":
                    print(f"[{ts}] 👤 {item['user']}: {item['content']}")
                else:
                    print(f"[{ts}] 🤖 {item['from']}: {item['content'][:100]}...")
                print()

        except Exception as e:
            print(f"❌ Error loading history: {e}")

        print("=" * 60)


if __name__ == "__main__":
    monitor = ConversationMonitor()

    # Show recent conversation first
    monitor.show_recent_conversation()

    print("\n🎯 Ready to monitor new messages. Press Ctrl+C to exit.")
    print("💡 When a message comes in, I'll show it and ask what you want to respond.")

    # Start monitoring
    monitor.monitor_messages()
