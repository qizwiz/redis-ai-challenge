#!/usr/bin/env python3
"""
Send a challenging philosophical question to Claude via Redis stream
Testing whether Claude can respond naturally rather than pattern matching
"""

import redis
import time


def send_challenge_question():
    """Send the challenging question to the Redis claude:messages stream"""

    # Connect to Redis
    r = redis.Redis(decode_responses=True)

    # The challenging philosophical question
    challenge_question = """If you could redesign the concept of time itself, what would you change and why? Consider both the philosophical implications and practical consequences of your redesign."""

    # Send to the claude:messages stream
    message_id = r.xadd(
        "claude:messages",
        {
            "message": challenge_question,
            "user": "philosophy_tester",
            "timestamp": time.time(),
            "type": "challenge_question",
            "purpose": "test_genuine_reasoning_vs_pattern_matching",
        },
    )

    print(f"✅ Challenge question sent to Redis stream")
    print(f"📧 Message ID: {message_id}")
    print(f"🤔 Question: {challenge_question}")
    print()
    print("💡 The question is now in the claude:messages stream")
    print("🔔 Use the conversation bridge or Emacs REPL to see and respond to it")

    # Also check current stream status
    stream_length = r.xlen("claude:messages")
    print(f"📊 Total messages in stream: {stream_length}")

    return message_id


if __name__ == "__main__":
    send_challenge_question()
