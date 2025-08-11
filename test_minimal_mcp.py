#!/usr/bin/env python3
"""
Minimal MCP server to test basic functionality
"""

import asyncio
from mcp.server import Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

# Create server
server = Server("test-mcp")


@server.list_tools()
async def list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="test_tool",
                description="A simple test tool",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "Message to echo"}
                    },
                },
            )
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls"""
    if name == "test_tool":
        message = arguments.get("message", "Hello from MCP!")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Echo: {message}")]
        )

    return CallToolResult(
        content=[TextContent(type="text", text=f"Unknown tool: {name}")]
    )


async def main():
    """Run the test MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
