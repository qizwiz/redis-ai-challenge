#!/usr/bin/env python3
"""
Test the debug MCP server to understand the exact issue
"""

import asyncio
import json
import sys


async def test_debug_server():
    """Test debug MCP server with detailed error catching"""
    print("Testing debug MCP server...")

    try:
        # Start the debug server
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "debug_mcp_decorators.py",
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Allow server to start
        await asyncio.sleep(0.5)

        # Initialize
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "clientInfo": {"name": "debug-client", "version": "1.0.0"},
            },
        }

        request_data = json.dumps(init_request) + "\n"
        print(f"Sending: {request_data.strip()}")
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Read initialization response
        init_response = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
        print(f"Received: {init_response.decode().strip()}")
        init_result = json.loads(init_response.decode().strip())

        if "result" in init_result:
            print("✅ Initialization successful")
        else:
            print(f"❌ Initialization failed: {init_result}")
            return False

        # Send initialized notification
        initialized_notification = {
            "jsonrpc": "2.0",
            "method": "notifications/initialized",
        }

        request_data = json.dumps(initialized_notification) + "\n"
        print(f"Sending: {request_data.strip()}")
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Small delay for notification processing
        await asyncio.sleep(0.1)

        # Test tools list
        tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }

        request_data = json.dumps(tools_request) + "\n"
        print(f"Sending: {request_data.strip()}")
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Read tools response
        tools_response = await asyncio.wait_for(proc.stdout.readline(), timeout=5.0)
        print(f"Received: {tools_response.decode().strip()}")
        tools_result = json.loads(tools_response.decode().strip())

        if "result" in tools_result:
            tools = tools_result["result"].get("tools", [])
            print(f"✅ Found {len(tools)} tools")
            for tool in tools:
                print(f"  - {tool}")

            # Test tool call if tools exist
            if tools:
                tool_call_request = {
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {"name": "debug_tool", "arguments": {}},
                }

                request_data = json.dumps(tool_call_request) + "\n"
                print(f"Sending: {request_data.strip()}")
                proc.stdin.write(request_data.encode())
                await proc.stdin.drain()

                # Read tool call response
                call_response = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=5.0
                )
                print(f"Received: {call_response.decode().strip()}")
                call_result = json.loads(call_response.decode().strip())

                if "result" in call_result:
                    print("✅ Tool call successful")
                    content = call_result["result"].get("content", [])
                    for item in content:
                        print(f"   Content: {item}")
                else:
                    print(f"❌ Tool call failed: {call_result}")

        else:
            print(f"❌ Tools list failed: {tools_result}")

            # Check stderr for any Python errors
            stderr_output = await proc.stderr.read()
            if stderr_output:
                print(f"STDERR: {stderr_output.decode()}")

        # Clean up
        proc.terminate()
        await proc.wait()

        return "result" in tools_result

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        if "proc" in locals():
            proc.terminate()
            await proc.wait()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_debug_server())
    print(f"Test {'PASSED' if success else 'FAILED'}")
    sys.exit(0 if success else 1)
