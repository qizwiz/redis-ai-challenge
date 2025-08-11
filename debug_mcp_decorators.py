#!/usr/bin/env python3
"""
Debug MCP decorator behavior
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
server = Server("debug-mcp")

print("Server created, examining decorators...")

# Try to understand what the decorator expects
print("list_tools decorator:", server.list_tools)
print("call_tool decorator:", server.call_tool)


# Let's try registering a simple function and see what happens
@server.list_tools()
async def my_list_tools():
    print("my_list_tools called, returning tools...")
    tools = [
        Tool(
            name="debug_tool",
            description="Debug tool",
            inputSchema={"type": "object", "properties": {}},
        )
    ]
    result = ListToolsResult(tools=tools)
    print(f"Returning ListToolsResult with {len(tools)} tools")
    print(f"Result type: {type(result)}")
    print(f"Result dict: {result.model_dump()}")
    return result


@server.call_tool()
async def my_call_tool(name: str, arguments: dict):
    print(f"my_call_tool called with name={name}, arguments={arguments}")
    result = CallToolResult(content=[TextContent(type="text", text=f"Debug: {name}")])
    print(f"Returning CallToolResult: {result.model_dump()}")
    return result


print("Functions registered, checking server state...")
print("Server handlers:", hasattr(server, "request_handlers"))


async def main():
    """Run debug server with detailed logging"""
    print("Starting debug server...")
    async with stdio_server() as (read_stream, write_stream):
        print("Stdio server started, running main server...")
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    print("Running debug MCP server...")
    asyncio.run(main())
