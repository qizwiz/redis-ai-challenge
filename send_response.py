#!/usr/bin/env python3
"""
Quick Response Sender - Send a response to the Redis conversation stream
"""

import redis
import time
import sys


def send_response(message):
    """Send a response to the claude:responses stream"""
    redis_client = redis.Redis(decode_responses=True)

    response_data = {
        "response": message,
        "timestamp": str(time.time()),
        "from": "claude-interactive",
        "conversation_mode": "interactive",
    }

    try:
        result = redis_client.xadd("claude:responses", response_data)
        print(f"✅ Response sent! ID: {result}")
        print(f"📤 Message: {message}")
        return result
    except Exception as e:
        print(f"❌ Failed to send response: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python send_response.py 'Your message here'")
        sys.exit(1)

    message = " ".join(sys.argv[1:])
    send_response(message)
