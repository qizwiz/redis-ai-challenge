#!/usr/bin/env python3
"""
Claude REPL Status - Check for messages from Emacs
Simple status checker for use with claude-code
"""

import redis
import sys


def main():
    """Check status and show any pending messages"""
    try:
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)

        # Check for current message
        message = r.get("claude:current_message")
        timestamp = r.get("claude:timestamp")

        if message:
            print("🔔 CLAUDE REPL MESSAGE WAITING")
            print("=" * 50)
            print(f"Message: {message}")
            if timestamp:
                print(f"Timestamp: {timestamp}")
            print()
            print("To respond:")
            print(f"  python3 claude_repl_bridge.py")
            print("  OR use claude-code -r to handle interactively")
        else:
            print("✅ No pending messages from Claude REPL")

        # Check Redis connection
        info = r.info("server")
        print(f"📡 Redis server: {info.get('redis_version', 'Unknown')}")

    except redis.ConnectionError:
        print("❌ Could not connect to Redis. Make sure Redis is running.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
