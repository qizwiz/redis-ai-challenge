#!/usr/bin/env python3
"""
Complete test of Claude REPL system
Tests the full loop: Emacs -> Redis -> Bridge -> Claude -> Redis -> Emacs
"""

import redis
import subprocess
import time
import os


def test_claude_repl_system():
    """Test the complete Claude REPL system"""

    print("🧪 Testing Claude REPL Complete System")
    print("=" * 50)

    # Connect to Redis
    r = redis.Redis(decode_responses=True)

    # Clear any existing messages
    print("🧹 Clearing Redis streams...")
    r.delete("claude:messages", "claude:responses")

    # 1. Test loading claude_repl.el
    print("\n1️⃣ Testing claude_repl.el loading...")
    result = subprocess.run(
        [
            "emacs",
            "--batch",
            "--eval",
            '(load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")',
            "--eval",
            '(message "✅ claude_repl.el loaded successfully")',
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ claude_repl.el loads without errors")
    else:
        print(f"❌ Error loading claude_repl.el: {result.stderr}")
        return False

    # 2. Simulate sending a message from Emacs to Redis
    print("\n2️⃣ Simulating Emacs message to Redis...")
    test_message = "Hello Claude! This is a test from the REPL system."

    message_id = r.xadd(
        "claude:messages",
        {"message": test_message, "user": "test_user", "timestamp": str(time.time())},
    )
    print(f"✅ Message added to Redis stream: {message_id}")

    # 3. Check if message is in Redis
    print("\n3️⃣ Verifying message in Redis...")
    messages = r.xrange("claude:messages")
    if messages:
        print(f"✅ Found {len(messages)} message(s) in Redis")
        for msg_id, fields in messages:
            print(f"   📨 {fields.get('message', '')}")
    else:
        print("❌ No messages found in Redis")
        return False

    # 4. Start bridge and wait for processing
    print("\n4️⃣ Starting bridge to process message...")
    print("   (Bridge will process the message and send response)")

    # Start bridge subprocess
    bridge_process = subprocess.Popen(
        ["python3", "claude_repl_bridge.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Wait a bit for processing
    print("   ⏳ Waiting for bridge to process message...")
    time.sleep(5)

    # 5. Check for response in Redis
    print("\n5️⃣ Checking for Claude response...")
    responses = r.xrange("claude:responses")

    if responses:
        print(f"✅ Found {len(responses)} response(s) from Claude")
        for resp_id, fields in responses:
            response_text = fields.get("response", "")
            print(f"   🤖 Claude: {response_text[:100]}...")
    else:
        print("❌ No responses found from Claude")

        # Check if bridge is still running
        if bridge_process.poll() is None:
            print("   Bridge is still running, waiting a bit more...")
            time.sleep(3)
            responses = r.xrange("claude:responses")
            if responses:
                print(f"✅ Found {len(responses)} response(s) from Claude (after wait)")
                for resp_id, fields in responses:
                    response_text = fields.get("response", "")
                    print(f"   🤖 Claude: {response_text[:100]}...")

    # 6. Test Emacs integration with a real Elisp script
    print("\n6️⃣ Testing Emacs integration script...")

    # Create a test Elisp script
    elisp_test = """
(progn
  (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")
  (message "✅ Claude REPL system ready!")
  (message "🎯 To test: Run (claude-repl) to start the interface")
  (message "📋 Current messages in Redis: %s"
           (shell-command-to-string "redis-cli XLEN claude:messages"))
  (message "📨 Current responses in Redis: %s" 
           (shell-command-to-string "redis-cli XLEN claude:responses")))
"""

    result = subprocess.run(
        ["emacs", "--batch", "--eval", elisp_test], capture_output=True, text=True
    )

    print(f"Emacs integration test output:")
    print(result.stdout)

    # Clean up
    print("\n🧹 Cleanup...")
    bridge_process.terminate()
    bridge_process.wait()

    print("\n✅ Claude REPL System Test Complete!")
    print("\n📋 To use the system:")
    print(
        '   1. Load in Emacs: (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl.el")'
    )
    print("   2. Start REPL: (claude-repl)")
    print("   3. Start bridge: python3 claude_repl_bridge.py")
    print("   4. Type messages in the *Claude-REPL* buffer and press RET")

    return True


if __name__ == "__main__":
    test_claude_repl_system()
