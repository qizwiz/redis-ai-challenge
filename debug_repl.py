#!/usr/bin/env python3
"""
Debug what's wrong with Redis communication
"""

import redis

redis_client = redis.Redis(decode_responses=True)

print("=== DEBUG REDIS COMMUNICATION ===")

# Check what messages exist
messages = redis_client.xrange("claude:messages", count=10)
print(f"Messages in claude:messages: {len(messages)}")
for msg_id, fields in messages:
    print(f"  {msg_id}: {fields}")

# Try to add and read a simple response
print("\n=== TESTING RESPONSE WRITING ===")
response_id = redis_client.xadd(
    "claude:responses", {"response": "Debug test response", "timestamp": 12345}
)
print(f"Added response with ID: {response_id}")

responses = redis_client.xrange("claude:responses", count=10)
print(f"Responses in claude:responses: {len(responses)}")
for resp_id, fields in responses:
    print(f"  {resp_id}: {fields}")
