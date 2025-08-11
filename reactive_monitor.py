#!/usr/bin/env python3
"""
Reactive Monitor - Watch Redis streams for real-time Emacs changes
"""
import redis
import time
import threading


class ReactiveMonitor:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.last_stream_id = "0"
        self.monitoring = False

    def start_monitoring(self):
        """Start monitoring Redis streams for changes"""
        self.monitoring = True
        print("🔥 REACTIVE MONITORING STARTED")
        print("Watching for real-time Emacs state changes...")
        print("-" * 50)

        while self.monitoring:
            try:
                # Block and wait for new stream entries
                result = self.redis_client.xread(
                    {"emacs:changes": self.last_stream_id},
                    count=1,
                    block=1000,  # Block for 1 second
                )

                if result:
                    stream_name, messages = result[0]
                    for message_id, fields in messages:
                        self.handle_state_change(message_id, fields)
                        self.last_stream_id = message_id

            except KeyboardInterrupt:
                print("\n⏹️  Monitoring stopped")
                break
            except Exception as e:
                print(f"❌ Monitor error: {e}")
                time.sleep(1)

    def handle_state_change(self, message_id, fields):
        """Handle a state change event"""
        buffer_name = fields.get("buffer", "?")
        point = fields.get("point", "?")
        line = fields.get("line", "?")
        content = fields.get("content", "?")
        timestamp = fields.get("timestamp", "?")

        print(f"🔄 [{timestamp}] CHANGE DETECTED:")
        print(f"   Buffer: {buffer_name}")
        print(f"   Line {line}, Point {point}")
        if content.strip():
            print(f"   Content: '{content[:50]}{'...' if len(content) > 50 else ''}'")
        print()

        # Here's where AI would react to the changes
        self.ai_react_to_change(buffer_name, line, content)

    def ai_react_to_change(self, buffer_name, line, content):
        """AI reaction to state changes"""
        # This is where intelligent responses would go
        if "error" in content.lower():
            print("🤖 AI: I notice there might be an error in your code")
        elif buffer_name.endswith(".py"):
            print("🤖 AI: Working on Python code")
        elif buffer_name == "*scratch*":
            print("🤖 AI: Experimenting in scratch buffer")

    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False


if __name__ == "__main__":
    monitor = ReactiveMonitor()
    monitor.start_monitoring()
