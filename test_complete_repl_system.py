#!/usr/bin/env python3
"""
Complete Claude REPL System Test
Tests the full Emacs → Redis → Claude → Redis → Emacs conversation loop
"""

import redis
import subprocess
import time
import sys
import os
from pathlib import Path


def test_repl_system():
    """Test the complete REPL system"""

    print("🧪 Testing Complete Claude REPL System")
    print("=" * 50)

    # Initialize Redis
    r = redis.Redis(decode_responses=True)

    # Clear any existing data
    print("🧹 Clearing Redis...")
    r.delete("claude:messages", "claude:responses")

    # Test 1: Load Emacs file
    print("\n1️⃣ Testing Emacs file loading...")
    result = subprocess.run(
        [
            "emacs",
            "--batch",
            "--eval",
            '(progn (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl_fixed.el") (print \'loaded))',
        ],
        capture_output=True,
        text=True,
    )

    if result.returncode == 0:
        print("✅ Emacs claude_repl.el loads successfully")
    else:
        print(f"❌ Emacs loading failed: {result.stderr}")
        return False

    # Test 2: Send message from Emacs to Redis
    print("\n2️⃣ Testing Emacs → Redis message sending...")
    test_message = "Hello from the complete system test! Please confirm the Redis-MCP REPL is working."

    result = subprocess.run(
        [
            "emacs",
            "--batch",
            "--eval",
            f'(progn (load-file "/Users/jonathanhill/src/redis-ai-challenge/claude_repl_fixed.el") (claude-repl-send-to-redis "{test_message}") (print \'message-sent))',
        ],
        capture_output=True,
        text=True,
    )

    if "message-sent" in result.stdout:
        print("✅ Message sent from Emacs to Redis")
    else:
        print(f"❌ Message sending failed: {result.stderr}")
        return False

    # Verify message in Redis
    messages = r.xrange("claude:messages")
    if messages:
        print(f"✅ Message verified in Redis stream: {len(messages)} message(s)")
        for msg_id, fields in messages:
            print(f"   📨 {fields.get('message', '')[:50]}...")
    else:
        print("❌ No messages found in Redis")
        return False

    # Test 3: Process message through bridge
    print("\n3️⃣ Testing Redis → Claude → Redis via bridge...")

    # Start bridge process with timeout
    print("🌉 Starting bridge process...")
    bridge_process = subprocess.Popen(
        ["python3", "claude_repl_bridge.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # Wait for processing (max 30 seconds)
        for i in range(30):
            responses = r.xrange("claude:responses")
            if responses:
                print("✅ Bridge processed message and stored response")
                for resp_id, fields in responses:
                    response_text = fields.get("response", "")
                    print(f"   🤖 Claude responded: {response_text[:100]}...")
                break
            time.sleep(1)
            print(f"   ⏳ Waiting for bridge processing... ({i+1}/30)")
        else:
            print("❌ Bridge did not process message within timeout")
            return False
    finally:
        # Clean up bridge process
        bridge_process.terminate()
        try:
            bridge_process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            bridge_process.kill()

    # Test 4: Verify complete conversation loop
    print("\n4️⃣ Testing complete conversation loop...")

    # Check message was consumed
    remaining_messages = r.xrange("claude:messages")
    if not remaining_messages:
        print("✅ Original message was consumed by bridge")
    else:
        print(f"⚠️  {len(remaining_messages)} message(s) still in queue")

    # Check response exists
    responses = r.xrange("claude:responses")
    if responses:
        print("✅ Response available for Emacs to consume")

        # Test Emacs response retrieval (would normally happen in REPL buffer)
        print("\n5️⃣ Testing response retrieval...")

        # Simulate what Emacs REPL would do
        result = subprocess.run(
            ["redis-cli", "XRANGE", "claude:responses", "-", "+"],
            capture_output=True,
            text=True,
        )

        if result.returncode == 0 and result.stdout.strip():
            print("✅ Response successfully retrieved from Redis")
            print(f"   📋 Full conversation cycle complete!")
        else:
            print("❌ Could not retrieve response")
            return False
    else:
        print("❌ No response found in Redis")
        return False

    print("\n" + "=" * 50)
    print("🎉 COMPLETE CLAUDE REPL SYSTEM TEST: PASSED")
    print("✅ Emacs loads claude_repl.el")
    print("✅ Messages flow: Emacs → Redis → Claude → Redis → Emacs")
    print("✅ Bridge processes messages and generates responses")
    print("✅ Complete conversation loop is functional")
    print("\n🚀 System ready for interactive use!")

    return True


if __name__ == "__main__":
    try:
        success = test_repl_system()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        sys.exit(1)
