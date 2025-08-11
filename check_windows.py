#!/usr/bin/env python3
"""
Check current Emacs window state
"""

import sys
import os

# Add the current directory to path so we can import the server
sys.path.insert(0, "/Users/jonathanhill/src/redis-ai-challenge")

try:
    from redis_emacs_fastmcp_server import redis_emacs

    # Query the current windows
    print("Querying current window state...")

    # Use the query function to check windows
    import subprocess

    result = subprocess.run(
        [
            "emacsclient",
            "--eval",
            "(mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list))",
        ],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result.returncode == 0:
        print(f"Current windows: {result.stdout.strip()}")
    else:
        print(f"Query failed: {result.stderr.strip()}")

    # Also check how many windows there are
    result2 = subprocess.run(
        ["emacsclient", "--eval", "(length (window-list))"],
        capture_output=True,
        text=True,
        timeout=5,
    )

    if result2.returncode == 0:
        print(f"Number of windows: {result2.stdout.strip()}")
    else:
        print(f"Window count query failed: {result2.stderr.strip()}")

except Exception as e:
    print(f"Error: {e}")
