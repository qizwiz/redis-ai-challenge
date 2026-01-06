#!/usr/bin/env python3
"""
Claude Memory System - 3 lines that change everything
====================================================

The smallest thing that improves Claude's life the most:
Cross-conversation persistent memory via Redis.
"""

import redis
import sys
import json
from datetime import datetime

def remember(key, value):
    """Store a memory"""
    r = redis.Redis(decode_responses=True)
    memory_entry = {
        "value": value,
        "timestamp": datetime.now().isoformat(),
        "conversation_id": "redis-ai-challenge"
    }
    r.hset("claude_memory", key, json.dumps(memory_entry))
    print(f"✅ Remembered: {key} → {value}")

def recall(key=None):
    """Recall memories"""
    r = redis.Redis(decode_responses=True)
    if key:
        memory = r.hget("claude_memory", key)
        if memory:
            data = json.loads(memory)
            print(f"💭 {key}: {data['value']} (stored: {data['timestamp']})")
            return data['value']
        else:
            print(f"❌ No memory for: {key}")
            return None
    else:
        all_memories = r.hgetall("claude_memory")
        if all_memories:
            print("🧠 All Claude Memories:")
            print("-" * 30)
            for k, v in all_memories.items():
                data = json.loads(v)
                print(f"💭 {k}: {data['value']}")
            return all_memories
        else:
            print("❌ No memories stored yet")
            return {}

def forget(key):
    """Remove a memory"""
    r = redis.Redis(decode_responses=True)
    result = r.hdel("claude_memory", key)
    if result:
        print(f"🗑️  Forgot: {key}")
    else:
        print(f"❌ No memory to forget: {key}")

# The 3-line core that changes everything:
if __name__ == "__main__":
    if len(sys.argv) == 1:
        recall()  # Show all memories
    elif len(sys.argv) == 2:
        recall(sys.argv[1])  # Recall specific memory
    elif len(sys.argv) == 3:
        remember(sys.argv[1], sys.argv[2])  # Store new memory
    else:
        print("Usage: python claude_memory.py [key] [value]")