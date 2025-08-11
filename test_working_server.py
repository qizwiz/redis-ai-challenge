#!/usr/bin/env python3
"""
Test the working MCP server
"""

import asyncio
import json
import sys


async def test_working_server():
    """Test working MCP server"""
    print("Testing working MCP server...")

    try:
        # Start the working server
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "working_mcp_server.py",
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
        print(f"✅ Initialization successful")

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

            # Test echo tool call
            if tools:
                echo_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "test_echo",
                        "arguments": {"message": "Hello MCP!"},
                    },
                }

                request_data = json.dumps(echo_request) + "\n"
                proc.stdin.write(request_data.encode())
                await proc.stdin.drain()

                # Read echo response
                echo_response = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=3.0
                )
                echo_result = json.loads(echo_response.decode().strip())

                if "result" in echo_result:
                    content = echo_result["result"].get("content", [])
                    if content:
                        print(f"✅ Echo tool: {content[0].get('text')}")

                # Test status tool call
                status_request = {
                    "jsonrpc": "2.0",
                    "id": 4,
                    "method": "tools/call",
                    "params": {"name": "test_status", "arguments": {}},
                }

                request_data = json.dumps(status_request) + "\n"
                proc.stdin.write(request_data.encode())
                await proc.stdin.drain()

                # Read status response
                status_response = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=3.0
                )
                status_result = json.loads(status_response.decode().strip())

                if "result" in status_result:
                    content = status_result["result"].get("content", [])
                    if content:
                        print(f"✅ Status tool: {content[0].get('text')}")

            print("✅ All MCP communication working properly!")

        else:
            print(f"❌ Tools list failed: {tools_result.get('error')}")
            return False

        # Clean up
        proc.terminate()
        await proc.wait()

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        if "proc" in locals():
            proc.terminate()
            await proc.wait()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_working_server())
    sys.exit(0 if success else 1)
