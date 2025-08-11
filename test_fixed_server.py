#!/usr/bin/env python3
"""
Test the fixed MCP servers
"""

import asyncio
import json
import sys


async def test_fixed_server():
    """Test fixed recursive development MCP server"""
    print("Testing fixed recursive development MCP server...")

    try:
        # Start the fixed server
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "fixed_recursive_development_mcp.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Initialize
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

        # Read initialization response
        init_response = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)
        init_result = json.loads(init_response.decode().strip())
        print(f"✅ Initialization: {init_result.get('result', {}).get('capabilities')}")

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        request_data = json.dumps(initialized_notification) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Test tools list
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

        if "result" in tools_result:
            tools = tools_result["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                print(f"  - {tool.get('name')}: {tool.get('description')}")

            # Test tool call
            if tools:
                tool_call_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "monitor_documents", "arguments": {}},
                }

                request_data = json.dumps(tool_call_request) + "\n"
                proc.stdin.write(request_data.encode())
                await proc.stdin.drain()

                # Read tool call response
                call_response = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=3.0
                )
                call_result = json.loads(call_response.decode().strip())

                if "result" in call_result:
                    content = call_result["result"].get("content", [])
                    print(f"✅ Tool call successful!")
                    if content:
                        print(f"   Result: {content[0].get('text', '')[:100]}...")
                else:
                    print(f"❌ Tool call failed: {call_result.get('error')}")
        else:
            print(f"❌ Tools list failed: {tools_result.get('error')}")

        # Clean up
        proc.terminate()
        await proc.wait()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        if "proc" in locals():
            proc.terminate()
            await proc.wait()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_fixed_server())
    sys.exit(0 if success else 1)
