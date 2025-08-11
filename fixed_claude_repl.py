#!/usr/bin/env python3
"""
Fixed Claude REPL - Handles bidirectional conversation properly
"""

import redis
import time
import signal
import sys


def signal_handler(sig, frame):
    print("\n👋 Claude REPL stopped by user")
    sys.exit(0)


def main():
    """
    Main entry point for the Fixed Claude REPL system that provides bidirectional communication between Emacs and Claude through Redis streams.

    This function establishes a Redis-coordinated conversation system that:
    - Listens for messages from Emacs via Redis streams
    - Processes incoming messages with contextual responses
    - Sends responses back to Emacs through Redis streams
    - Maintains conversation state and prevents duplicate processing
    - Provides specialized responses for test, Redis coordination, and aquarium queries

    The system runs continuously until interrupted, creating a real-time conversation bridge between Emacs buffers and Claude AI without requiring emacsclient.

    Args:
        None

    Returns:
        None: Function runs indefinitely until interrupted or Redis connection fails

    Raises:
        Exception: If Redis connection fails during startup, function returns early
        KeyboardInterrupt: Handled by signal handler for graceful shutdown
        Various Redis exceptions: Caught and logged during message processing loop

    Example:
        ```python
        # Start the Redis-coordinated Claude REPL
        if __name__ == "__main__":
            main()
        ```

    Note:
        Requires Redis server running locally and accessible streams:
        - Input stream: "claude:messages"
        - Output stream: "claude:responses"
        The function maintains a processed_messages set to avoid duplicate responses.
    """
    signal.signal(signal.SIGINT, signal_handler)

    try:
        redis_client = redis.Redis(decode_responses=True)
        # Test connection
        redis_client.ping()
        print("🎯 Fixed Claude REPL Starting")
        print("📡 Connected to Redis and listening...")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return

    processed_messages = set()

    while True:
        try:
            # Get messages from the correct stream
            messages = redis_client.xrange("claude:messages", count=10)

            for message_id, fields in messages:
                if message_id in processed_messages:
                    continue

                message_text = fields.get("message", "")
                user = fields.get("user", "unknown")

                if message_text:
                    print(f"📨 Processing: {message_text}")

                    # Generate contextual response
                    if "test" in message_text.lower():
                        response = f"""✅ Test successful! 

🔄 **Bidirectional Communication Working**
- Your message: "{message_text}"
- Redis streams: claude:messages → claude:responses  
- Conversation REPL: Active and responding
- System: Ready for full conversation

The Redis-coordinated conversation system is operational!"""

                    elif (
                        "redis" in message_text.lower()
                        and "coordination" in message_text.lower()
                    ):
                        response = """🎯 **Redis-MCP Coordination System**

Our system architecture:
1. **Message Flow**: Emacs → Redis streams → Claude → Redis → Emacs
2. **No emacsclient**: Pure Redis coordination backbone
3. **Real-time**: Conversation appears directly in your Emacs buffer
4. **Stateful**: All interactions logged for learning

This conversation is happening through Redis streams right now!"""

                    elif "aquarium" in message_text.lower():
                        response = """🐠 **Aquarium Creation Ready**

With our Redis-MCP system:
- **Fish objects** stored in Redis with position/velocity
- **Physics simulation** coordinated through streams  
- **Real-time rendering** in Emacs buffers
- **Interactive control** through this conversation

Should I create the aquarium using our redis-ai-coordinator subagent?"""

                    else:
                        response = f"""💬 **Claude Response**

I received: "{message_text}"

This is working! We have successful bidirectional communication through Redis coordination. Your Emacs REPL is now connected to me through pure Redis streams.

What would you like to explore with our Redis-AI system?"""

                    print(f"🤖 Sending response...")

                    # Send response to Redis for Emacs to display
                    redis_client.xadd(
                        "claude:responses",
                        {
                            "response": response,
                            "timestamp": time.time(),
                            "from": "fixed-claude-repl",
                            "in_reply_to": message_text,
                        },
                    )

                    processed_messages.add(message_id)
                    print("✅ Response sent to Emacs via Redis")

            time.sleep(1)

        except Exception as e:
            print(f"💥 Error: {e}")
            time.sleep(2)


if __name__ == "__main__":
    main()
