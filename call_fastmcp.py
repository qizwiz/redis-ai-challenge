#!/usr/bin/env python3
"""
Quick script to call the redis-emacs FastMCP server to split window to the right
"""

import asyncio
import json
import subprocess
import sys


async def call_fastmcp_tool():
    """Call the redis-emacs FastMCP server with a command"""

    # Start the FastMCP server
    process = subprocess.Popen(
        [
            "python3",
            "/Users/jonathanhill/src/redis-ai-challenge/redis_emacs_fastmcp_server.py",
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # FastMCP uses simpler protocol - just send tool call
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "emacs_command",
            "arguments": {"command": "split window right"},
        },
    }

    try:
        # Send the tool call
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        # Read the response
        response = process.stdout.readline()

        if response:
            result = json.loads(response)
            if "result" in result:
                print(result["result"])
            else:
                print(f"Error: {result}")
        else:
            print("No response received")

    except Exception as e:
        print(f"Error calling FastMCP tool: {e}")
    finally:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    asyncio.run(call_fastmcp_tool())
