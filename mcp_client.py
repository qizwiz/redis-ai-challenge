#!/usr/bin/env python3
"""
A generic and robust MCP client to call any tool on any MCP server.
Handles the full initialization handshake correctly.
"""

import asyncio
import json
import subprocess
import sys
import os
import time

DEFAULT_EMACS_SERVER = os.path.join(os.path.dirname(__file__), "redis_emacs_fastmcp_server.py")

async def call_mcp_tool(tool_name, tool_args, server_path):
    """Call a tool on a specified MCP server with correct handshake."""

    process = subprocess.Popen(
        ["python3", server_path],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )

    try:
        # 1. Send initialize request
        init_request = {
            "jsonrpc": "2.0", "id": 0, "method": "initialize",
            "params": {"clientInfo": {"name": "mcp-client", "version": "3.0.0"}}
        }
        process.stdin.write(json.dumps(init_request) + "\n")
        process.stdin.flush()

        # 2. Read and discard the initialize response
        init_response = process.stdout.readline()

        # 3. Send initialized notification (no response expected)
        initialized_notification = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
        process.stdin.write(json.dumps(initialized_notification) + "\n")
        process.stdin.flush()

        # Add a small delay to allow the server to process initialization
        time.sleep(0.1)

        # 4. Send the actual tool call request
        params = {"name": tool_name}
        # Arguments are now always a JSON string
        params["arguments"] = tool_args

        tool_request = {
            "jsonrpc": "2.0", "id": 1, "method": "tools/call",
            "params": params
        }
        process.stdin.write(json.dumps(tool_request) + "\n")
        process.stdin.flush()

        # 5. Read the tool call response
        tool_response = process.stdout.readline()

        if tool_response:
            result = json.loads(tool_response)
            if "result" in result:
                print(json.dumps(result["result"], indent=2))
            elif "error" in result:
                print(f"Error from server: {json.dumps(result['error'], indent=2)}")
            else:
                print(f"Unknown response format: {tool_response}")
        else:
            print("No response received for tool call.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        process.terminate()
        process.wait()



def print_usage():
    print("Usage: python mcp_client.py <tool_name> '<json_arguments>' [server_path]")
    print("\nExample:")
    print("  python mcp_client.py get_context_stats '{}' ./context_manager_agent.py")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print_usage()
        sys.exit(1)

    tool_name = sys.argv[1]
    try:
        tool_args = json.loads(sys.argv[2])
    except json.JSONDecodeError:
        print("Error: Invalid JSON for arguments.", file=sys.stderr)
        sys.exit(1)

    server_path = DEFAULT_EMACS_SERVER
    if len(sys.argv) > 3:
        server_path = sys.argv[3]

    if not os.path.exists(server_path):
        print(f"Error: Server path not found at '{server_path}'", file=sys.stderr)
        sys.exit(1)

    asyncio.run(call_mcp_tool(tool_name, tool_args, server_path))
