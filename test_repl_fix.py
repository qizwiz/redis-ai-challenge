#!/usr/bin/env python3
"""
Test script to verify the Claude REPL conversation loop
"""

import redis
import time

# Test the complete conversation loop
redis_client = redis.Redis(decode_responses=True)

print("🧪 Testing Claude REPL conversation loop...")

# 1. Send a test message to the user input stream
print("1. Sending test message to claude_repl:user_input...")
redis_client.xadd(
    "claude_repl:user_input",
    {
        "message": "test repl connection",
        "user": "test_user",
        "timestamp": str(time.time()),
    },
)

# 2. Check what's in the user input stream
print("2. Messages in claude_repl:user_input:")
messages = redis_client.xrange("claude_repl:user_input", "-", "+", count=5)
for msg_id, fields in messages:
    print(f"   {msg_id}: {fields}")

# 3. Wait a moment for bridge to process
print("3. Waiting 3 seconds for bridge to process...")
time.sleep(3)

# 4. Check for responses in emacs:commands
print("4. Responses in emacs:commands:")
responses = redis_client.xrange("emacs:commands", "-", "+", count=5)
if responses:
    for resp_id, fields in responses:
        print(f"   {resp_id}: {fields}")
else:
    print("   No responses found")

# 5. Test manual response insertion
print("5. Manually inserting test response...")
redis_client.xadd(
    "emacs:commands",
    {"text": "\n\nClaude> This is a test response from the bridge!\n\nYou> "},
)

print("6. Checking emacs:commands again:")
responses = redis_client.xrange("emacs:commands", "-", "+", count=5)
for resp_id, fields in responses:
    print(f"   {resp_id}: {fields}")

print("✅ Test complete. If bridge is working, step 4 should show responses.")
