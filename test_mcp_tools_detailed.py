#!/usr/bin/env python3
"""
Detailed MCP server tools testing
"""

import asyncio
import json
import sys


async def test_server_tools(server_script: str, server_name: str):
    """Test MCP server tools list functionality"""
    print(f"\n=== Testing {server_name} Tools ===")

    try:
        # Start the MCP server process
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send MCP initialization
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "test-client", "version": "1.0.0"},
            },
        }

        request_data = json.dumps(init_request) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Wait for initialization response
        init_response = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
        init_result = json.loads(init_response.decode().strip())
        print(
            f"Initialization: {init_result.get('result', {}).get('capabilities', 'No capabilities')}"
        )

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        request_data = json.dumps(initialized_notification) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Send tools list request
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        request_data = json.dumps(tools_request) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Read tools response
        tools_response = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
        tools_result = json.loads(tools_response.decode().strip())

        print(f"Tools response: {tools_result}")

        if "result" in tools_result:
            tools = tools_result["result"].get("tools", [])
            print(f"Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description')}")
                if "inputSchema" in tool:
                    schema = tool["inputSchema"]
                    if "properties" in schema:
                        print(f"    Parameters: {list(schema['properties'].keys())}")
        elif "error" in tools_result:
            print(f"Error: {tools_result['error']}")

        # Test a simple tool call if tools are available
        if "result" in tools_result and tools_result["result"].get("tools"):
            first_tool = tools_result["result"]["tools"][0]
            tool_name = first_tool["name"]

            print(f"\nTesting tool call: {tool_name}")

            tool_call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {"name": tool_name, "arguments": {}},
            }

            request_data = json.dumps(tool_call_request) + "\n"
            proc.stdin.write(request_data.encode())
            await proc.stdin.drain()

            # Read tool call response
            call_response = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
            call_result = json.loads(call_response.decode().strip())

            print(f"Tool call response: {call_result}")

            if "result" in call_result:
                content = call_result["result"].get("content", [])
                if content:
                    print(f"Tool returned {len(content)} content items")
                    for item in content:
                        if item.get("type") == "text":
                            text = item.get("text", "")
                            print(f"  Text: {text[:100]}...")
            elif "error" in call_result:
                print(f"Tool call error: {call_result['error']}")

        # Clean up
        proc.terminate()
        await proc.wait()

    except Exception as e:
        print(f"Error testing {server_name}: {e}")
        if "proc" in locals():
            proc.terminate()
            await proc.wait()


async def main():
    """Test tools for both servers"""
    servers = [
        ("recursive_development_mcp.py", "Recursive Development MCP"),
        ("ai_emacs_integration_server.py", "AI Emacs Integration MCP"),
    ]

    for script, name in servers:
        await test_server_tools(script, name)


if __name__ == "__main__":
    asyncio.run(main())
