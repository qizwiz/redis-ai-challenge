#!/usr/bin/env python3
"""
Test MCP server communication using direct stdio protocol
"""

import asyncio
import json
import subprocess
import sys
from typing import Dict, Any


async def test_mcp_server(server_script: str, server_name: str) -> Dict[str, Any]:
    """Test MCP server communication"""
    print(f"\n=== Testing {server_name} ===")

    try:
        # Start the MCP server process
        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            server_script,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        # Send MCP initialization request
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

        # Send the request
        request_data = json.dumps(init_request) + "\n"
        proc.stdin.write(request_data.encode())
        await proc.stdin.drain()

        # Read response with timeout
        try:
            response_data = await asyncio.wait_for(proc.stdout.readline(), timeout=3.0)

            if response_data:
                response = json.loads(response_data.decode().strip())
                print(f"✅ {server_name} responded to initialization")
                print(f"   Response ID: {response.get('id')}")
                print(f"   Has result: {'result' in response}")
                print(f"   Has error: {'error' in response}")

                # Test tools list
                tools_request = {"jsonrpc": "2.0", "id": 2, "method": "tools/list"}

                request_data = json.dumps(tools_request) + "\n"
                proc.stdin.write(request_data.encode())
                await proc.stdin.drain()

                # Read tools response
                tools_response_data = await asyncio.wait_for(
                    proc.stdout.readline(), timeout=3.0
                )

                if tools_response_data:
                    tools_response = json.loads(tools_response_data.decode().strip())
                    tools = tools_response.get("result", {}).get("tools", [])
                    print(f"   Available tools: {len(tools)}")
                    for tool in tools:
                        print(
                            f"     - {tool.get('name')}: {tool.get('description', '')[:50]}..."
                        )

                    result = {
                        "status": "success",
                        "initialization": True,
                        "tools_count": len(tools),
                        "tools": [tool.get("name") for tool in tools],
                    }
                else:
                    result = {
                        "status": "partial",
                        "initialization": True,
                        "tools_count": 0,
                        "error": "No tools response",
                    }
            else:
                result = {
                    "status": "failed",
                    "initialization": False,
                    "error": "No initialization response",
                }
                print(f"❌ {server_name} did not respond to initialization")

        except asyncio.TimeoutError:
            result = {
                "status": "timeout",
                "initialization": False,
                "error": "Server response timeout",
            }
            print(f"⏰ {server_name} timed out")

        # Clean up
        proc.terminate()
        await proc.wait()

        return result

    except Exception as e:
        print(f"❌ {server_name} failed to start: {e}")
        return {"status": "failed", "initialization": False, "error": str(e)}


async def main():
    """Test both MCP servers"""
    print("Testing MCP Server Communication")
    print("=" * 40)

    # Test servers
    servers = [
        ("recursive_development_mcp.py", "Recursive Development MCP"),
        ("ai_emacs_integration_server.py", "AI Emacs Integration MCP"),
    ]

    results = {}

    for script, name in servers:
        results[name] = await test_mcp_server(script, name)

    # Summary
    print("\n" + "=" * 40)
    print("SUMMARY")
    print("=" * 40)

    for server_name, result in results.items():
        status_icon = (
            "✅"
            if result["status"] == "success"
            else "❌" if result["status"] == "failed" else "⚠️"
        )
        print(f"{status_icon} {server_name}: {result['status']}")
        if result.get("tools_count", 0) > 0:
            print(f"   Tools available: {result['tools_count']}")
            print(f"   Tool names: {', '.join(result.get('tools', []))}")
        if result.get("error"):
            print(f"   Error: {result['error']}")

    # Check if Redis is available
    print("\n" + "=" * 40)
    print("REDIS CONNECTIVITY CHECK")
    print("=" * 40)

    try:
        import redis

        r = redis.Redis(decode_responses=True)
        r.ping()
        print("✅ Redis is available and responding")
    except Exception as e:
        print(f"❌ Redis is not available: {e}")
        print("   Some MCP features may not work without Redis")


if __name__ == "__main__":
    asyncio.run(main())
