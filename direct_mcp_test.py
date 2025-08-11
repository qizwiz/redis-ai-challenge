#!/usr/bin/env python3
"""
Direct MCP Server Connection Test
Bypassing Claude Code's interface to test servers directly
"""

import asyncio
import json
import subprocess
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def test_mcp_server(server_file, server_name):
    """Test direct connection to an MCP server"""
    print(f"🔌 Testing direct connection to {server_name}")
    
    try:
        # Create server parameters
        server_params = StdioServerParameters(
            command="python3",
            args=[server_file]
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                result = await session.initialize()
                print(f"✅ Connected to {server_name}")
                print(f"📋 Server info: {result}")
                
                # List available tools
                tools = await session.list_tools()
                print(f"🔧 Available tools: {[tool.name for tool in tools.tools]}")
                
                # Try to call a tool if available
                if tools.tools:
                    first_tool = tools.tools[0]
                    print(f"🧪 Testing tool: {first_tool.name}")
                    
                    try:
                        # Prepare arguments based on tool schema
                        args = {}
                        if hasattr(first_tool, 'inputSchema') and first_tool.inputSchema:
                            properties = first_tool.inputSchema.get('properties', {})
                            for prop_name, prop_info in properties.items():
                                args[prop_name] = f"test_{prop_name}"
                        
                        # Call the tool
                        result = await session.call_tool(first_tool.name, args)
                        print(f"🎯 Tool result: {result.content}")
                        
                        return True
                        
                    except Exception as e:
                        print(f"⚠️ Tool call failed: {e}")
                        return True  # Server connected, tool just failed
                else:
                    print("ℹ️ No tools available but server connected")
                    return True
                    
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

async def test_all_servers():
    """Test all available MCP servers directly"""
    
    servers_to_test = [
        ("jit_api_call_server.py", "jit-api-call"),
        ("mcp_redis_lisp_server.py", "redis-lisp"), 
        ("emacs_persistent_vision_mcp.py", "emacs-vision"),
    ]
    
    results = {}
    
    for server_file, server_name in servers_to_test:
        print(f"\n{'='*50}")
        result = await test_mcp_server(server_file, server_name)
        results[server_name] = result
        
    print(f"\n🏁 FINAL RESULTS:")
    print("="*50)
    for server_name, success in results.items():
        status = "✅ WORKING" if success else "❌ FAILED"
        print(f"{server_name}: {status}")
    
    return results

if __name__ == "__main__":
    print("🚀 Direct MCP Server Connection Test")
    print("=" * 50)
    
    try:
        results = asyncio.run(test_all_servers())
        success_count = sum(1 for success in results.values() if success)
        total_count = len(results)
        
        print(f"\n📊 Summary: {success_count}/{total_count} servers working directly")
        
        if success_count > 0:
            print("💡 Some servers work directly - the issue is Claude Code's MCP interface")
        else:
            print("🔍 All servers failed - deeper investigation needed")
            
    except Exception as e:
        print(f"💥 Test framework failed: {e}")
        sys.exit(1)