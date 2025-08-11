#!/usr/bin/env python3

from fastmcp import FastMCP

# Create FastMCP server
mcp = FastMCP("Dynamic Test MCP")

@mcp.tool()
def test_dynamic_tool() -> str:
    """Test tool added dynamically during Claude session"""
    return "🚀 Dynamic MCP server is working!"

if __name__ == "__main__":
    mcp.run()