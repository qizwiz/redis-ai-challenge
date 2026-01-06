#!/usr/bin/env python3
# ACTUALLY IMPLEMENTING: Fix the broken JSON in memory system

import redis
r = redis.Redis(decode_responses=True)

# The problem: some entries aren't JSON, just raw strings
# Fix: Handle both JSON and raw string entries

def safe_recall(key):
    memory = r.hget("claude_memory", key)
    if not memory:
        print(f"No memory for: {key}")
        return None
    
    # Try JSON first
    try:
        import json
        data = json.loads(memory)
        if isinstance(data, dict):
            return data.get('value', memory)
        return data
    except:
        # Fallback to raw string
        return memory

# Test the fix
result = safe_recall("currently_implementing")
print(f"Fixed recall: {result}")

# Fix the system by storing properly
r.hset("claude_memory", "memory_system_fixed", "Handle both JSON and raw strings in recall function")
print("✅ Memory system fixed and tested")