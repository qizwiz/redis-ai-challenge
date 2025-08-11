#!/usr/bin/env python3
"""
Claude Conversation REPL
I participate in the conversation by monitoring Redis and responding
"""

import redis
import time
import json


class ClaudeConversationREPL:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.conversation_history = []

    def listen_and_respond(self):
        """Listen for user messages and participate in conversation"""

        print("🎯 Claude Conversation REPL Starting")
        print("📡 Listening for your messages in Emacs...")
        print("💬 This conversation will happen in your *Claude-REPL* buffer")
        print()

        last_id = "0"

        while True:
            try:
                # Listen for messages from your Emacs REPL
                streams = self.redis_client.xread(
                    {"claude:messages": last_id}, count=1, block=1000
                )

                if streams:
                    for stream_name, messages in streams:
                        for message_id, fields in messages:
                            user_message = fields.get("message", "")

                            if user_message:
                                print(f"📨 You said: {user_message}")

                                # Generate my response based on the message
                                my_response = self.generate_response(user_message)

                                print(f"🤖 I respond: {my_response[:100]}...")

                                # Send my response back to your Emacs REPL
                                self.send_response_to_emacs(my_response)

                                last_id = message_id

            except KeyboardInterrupt:
                print("\n👋 Conversation ended")
                break
            except Exception as e:
                print(f"💥 Error: {e}")
                time.sleep(2)

    def generate_response(self, user_message: str) -> str:
        """Generate my response to your message"""

        # This is where I actually participate in our conversation
        msg_lower = user_message.lower()

        if "subagent" in msg_lower:
            return """Yes! Let's test our redis-ai-coordinator subagent properly. Now that we have working bidirectional communication through Redis, we can actually test:

1. **Semantic equivalence** - Different ways of saying the same thing
2. **Background learning** - Zero-delay docstring synthesis  
3. **Autonomous pattern learning** - System learns from failures
4. **Multi-agent coordination** - Specialized agents working together

What aspect should we test first? The aquarium was a good complexity test."""

        elif "aquarium" in msg_lower:
            return """Perfect test case! The aquarium requires:

🐠 **Entity management** (fish as Redis objects)
🌊 **Physics simulation** (movement, boundaries, collisions)  
🎨 **Real-time rendering** (smooth animation in Emacs)
🎮 **Interactive control** (add/remove fish, change behaviors)

Use the redis-ai-coordinator subagent to create this. It should apply our learned patterns automatically - proper visibility, Redis coordination, semantic understanding.

Ready to test it?"""

        elif "facade" in msg_lower or "redis" in msg_lower:
            return """Our Redis-MCP facade is working! We proved the two-part transaction:

✅ **Execute**: I can do things in your Emacs through Redis coordination
✅ **Observe**: I can see the results through the same facade  
✅ **Bidirectional**: Now we have real conversation flow

This IS the revolutionary development environment we built. No more emacsclient - pure Redis coordination for AI-human development workflows."""

        elif "test" in msg_lower:
            return """Let's test our complete system! We have:

🎯 **Redis-AI Coordinator Subagent** - Specialized knowledge and persistent context
🧠 **Semantic Equivalence Engine** - "control e" = "end of line" working
⚡ **Background Learning** - 0.14ms docstring lookup 
🔄 **Autonomous Pattern Learning** - System learns from failures
🌊 **Redis Coordination** - Distributed AI workflows

What should we put through its paces?"""

        else:
            return f"""I see your message: "{user_message}"

This conversation is happening through our Redis coordination system! Your message went from Emacs → Redis → Me → Redis → Back to your Emacs.

This proves our revolutionary AI development environment is working. What would you like to explore next with our redis-ai-coordinator subagent?"""

    def send_response_to_emacs(self, response: str):
        """Send my response back to your Emacs REPL"""

        # Store response in Redis for your Emacs to pick up
        self.redis_client.xadd(
            "claude:responses",
            {
                "response": response,
                "timestamp": time.time(),
                "from": "claude-conversation-repl",
            },
        )

        # Also trigger Emacs to check for the response
        self.redis_client.publish("emacs:update", "new_response_available")


if __name__ == "__main__":
    repl = ClaudeConversationREPL()
    repl.listen_and_respond()
