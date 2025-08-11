#!/usr/bin/env python3
"""
Working MCP Server with proper tool registration
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
server = Server("working-test")


# Override the list_tools method directly
async def list_tools_handler() -> ListToolsResult:
    """Handle list tools request"""
    tools = [
        Tool(
            name="test_echo",
            description="Echo a message back",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Message to echo"}
                },
                "required": ["message"],
            },
        ),
        Tool(
            name="test_status",
            description="Get server status",
            inputSchema={"type": "object", "properties": {}, "required": []},
        ),
    ]
    return ListToolsResult(tools=tools)


async def call_tool_handler(name: str, arguments: dict) -> CallToolResult:
    """Handle tool call request"""
    if name == "test_echo":
        message = arguments.get("message", "No message provided")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Echo: {message}")]
        )
    elif name == "test_status":
        return CallToolResult(
            content=[TextContent(type="text", text="Server is running and functional!")]
        )
    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )


# Register the handlers using the decorator approach but with proper function signatures
@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return await list_tools_handler()


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    return await call_tool_handler(name, arguments)


async def main():
    """Run the working MCP server"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
