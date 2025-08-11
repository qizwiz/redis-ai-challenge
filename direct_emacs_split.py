#!/usr/bin/env python3
"""
Direct call to the Redis-Emacs tools to split window to the right
"""

import sys
import os

# Add the current directory to path so we can import the server
sys.path.insert(0, "/Users/jonathanhill/src/redis-ai-challenge")

try:
    # Import the server and call the function directly
    from redis_emacs_fastmcp_server import redis_emacs

    # Use the emacs_command function to split window right
    command = "split window right"
    print(f"Executing command: {command}")

    # Parse the command into elisp
    elisp_commands = redis_emacs.parse_natural_language(command)
    print(f"Generated elisp commands: {elisp_commands}")

    # Execute the command sequence
    result = redis_emacs.execute_elisp_sequence(elisp_commands)

    if result["success"]:
        print(f"✅ Success! Window split to the right.")
        print(f"Result: {result['result']}")
        print(f"Commands executed: {result['elisp']}")
    else:
        print(f"❌ Failed to split window.")
        print(f"Error: {result['error']}")
        print(f"Commands attempted: {result['elisp']}")

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure the redis_emacs_fastmcp_server.py is in the current directory")
except Exception as e:
    print(f"Execution error: {e}")
