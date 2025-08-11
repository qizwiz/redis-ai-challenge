#!/usr/bin/env python3
import redis
import subprocess

redis_client = redis.Redis(decode_responses=True)

# Add a test response
redis_client.xadd("emacs:commands", {"text": "Claude> This is the test message!"})

# Get the raw format as shell-command would see it
result = subprocess.run(
    ["redis-cli", "XRANGE", "emacs:commands", "-", "+", "COUNT", "10"],
    capture_output=True,
    text=True,
)

print("Raw shell command output:")
print(repr(result.stdout))
print("\nParsed by lines:")
lines = result.stdout.split("\n")
for i, line in enumerate(lines):
    print(f"Line {i}: {repr(line)}")
    if "text" in line:
        print(f"  -> Found 'text' in line {i}")
