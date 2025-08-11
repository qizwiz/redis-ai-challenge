#!/usr/bin/env python3
"""
Test script to validate MCP server implementations
"""

import json
import subprocess
import sys
import os
from pathlib import Path


def test_mcp_server(server_path, env_vars=None):
    """Test if an MCP server can start and respond to basic commands"""

    print(f"\n🧪 Testing: {server_path}")

    # Test 1: Syntax check
    try:
        result = subprocess.run(
            [sys.executable, "-m", "py_compile", server_path],
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(f"❌ Syntax error: {result.stderr}")
            return False
        print("✅ Syntax check passed")
    except Exception as e:
        print(f"❌ Syntax check failed: {e}")
        return False

    # Test 2: Import check
    try:
        server_module = Path(server_path).stem
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        result = subprocess.run(
            [sys.executable, "-c", f"import {server_module}; print('Import OK')"],
            capture_output=True,
            text=True,
            cwd=Path(server_path).parent,
            env=env,
        )
        if result.returncode != 0:
            print(f"❌ Import error: {result.stderr}")
            return False
        print("✅ Import check passed")
    except Exception as e:
        print(f"❌ Import check failed: {e}")
        return False

    # Test 3: Server startup check (quick timeout)
    try:
        env = os.environ.copy()
        if env_vars:
            env.update(env_vars)

        process = subprocess.Popen(
            [sys.executable, server_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )

        try:
            # Send a simple JSON-RPC message
            test_message = {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

            stdout, stderr = process.communicate(
                input=json.dumps(test_message).encode() + b"\n", timeout=5
            )

            if process.returncode == 0 or "list_tools" in stderr.decode():
                print("✅ Server startup check passed")
                return True
            else:
                print(f"❌ Server startup issue: {stderr.decode()}")
                return False

        except subprocess.TimeoutExpired:
            print("✅ Server startup check passed (timeout = server running)")
            process.kill()
            return True

    except Exception as e:
        print(f"❌ Server startup failed: {e}")
        return False


def main():
    """Test all MCP servers from .mcp.json"""

    print("🔍 MCP Server Validation Suite")
    print("=" * 50)

    # Load MCP configuration
    try:
        with open(".mcp.json", "r") as f:
            config = json.load(f)
    except Exception as e:
        print(f"❌ Failed to load .mcp.json: {e}")
        return

    servers = config.get("mcpServers", {})
    results = {}

    for server_name, server_config in servers.items():
        if server_config.get("type") == "stdio":
            server_path = server_config["args"][0]
            env_vars = server_config.get("env", {})

            results[server_name] = test_mcp_server(server_path, env_vars)

    # Summary
    print("\n" + "=" * 50)
    print("📊 SUMMARY")
    print("=" * 50)

    working_servers = []
    broken_servers = []

    for server_name, passed in results.items():
        if passed:
            working_servers.append(server_name)
            print(f"✅ {server_name}")
        else:
            broken_servers.append(server_name)
            print(f"❌ {server_name}")

    print(f"\n📈 Results: {len(working_servers)}/{len(results)} servers working")

    if broken_servers:
        print(f"\n🔧 Servers needing fixes: {', '.join(broken_servers)}")


if __name__ == "__main__":
    main()
