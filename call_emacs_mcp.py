#!/usr/bin/env python3
"""
Quick script to call the redis-emacs MCP server.
Accepts a natural language command and an optional path to the server script.
"""

import asyncio
import json
import subprocess
import sys

# Define the default server path
DEFAULT_SERVER_PATH = "/Users/jonathanhill/src/redis-ai-challenge/redis_emacs_fastmcp_server.py"

async def call_mcp_tool(command, server_path):
    """Call the redis-emacs MCP server with a command"""

    # Create the MCP request
    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "emacs_command", "arguments": {"command": command}},
    }

    # Start the MCP server
    process = subprocess.Popen(
        [
            "python3",
            server_path,
        ],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    # Send initialization first
    init_request = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "direct-caller", "version": "1.0.0"},
        },
    }

    try:
        # Send initialization
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # Read initialization response
        init_response = process.stdout.readline()

        # Send initialized notification
        initialized = {"jsonrpc": "2.0", "method": "notifications/initialized"}
        process.stdin.write(json.dumps(initialized) + "\n")
        process.stdin.flush()

        # Send the actual tool call
        process.stdin.write(json.dumps(request) + "\n")
        process.stdin.flush()

        # Read the response
        response = process.stdout.readline()

        if response:
            result = json.loads(response)
            if "result" in result:
                content = result["result"]["content"]
                if content and len(content) > 0:
                    print(content[0]["text"])
                else:
                    print("Command executed successfully")
            else:
                print(f"Error: {result}")
        else:
            print("No response received")

    except Exception as e:
        print(f"Error calling MCP tool: {e}")
    finally:
        process.terminate()
        process.wait()


if __name__ == "__main__":
    command = "split window right"
    server_path = DEFAULT_SERVER_PATH

    if len(sys.argv) > 1:
        command = sys.argv[1]
    if len(sys.argv) > 2:
        server_path = sys.argv[2]

    asyncio.run(call_mcp_tool(command, server_path))