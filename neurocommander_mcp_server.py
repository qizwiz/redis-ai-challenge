#!/usr/bin/env python3

"""
NeuroCommander MCP Server - AI's Own Digital Workspace
Gives AI complete desktop control through MCP interface
"""

import asyncio
import subprocess
import json
import sys
from typing import Any, Sequence
from mcp.server.models import InitializationOptions
from mcp.server import NotificationOptions, Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource, Tool, TextContent, ImageContent, EmbeddedResource
)

app = Server("neurocommander")

@app.list_resources()
async def handle_list_resources() -> list[Resource]:
    """List NeuroCommander resources"""
    return [
        Resource(
            uri="neurocommander://desktop/state",
            name="Desktop State",
            description="Complete desktop window state",
            mimeType="application/json",
        ),
        Resource(
            uri="neurocommander://facade/realtime", 
            name="Facade Stream",
            description="Real-time facade events",
            mimeType="application/json",
        )
    ]

@app.read_resource()
async def handle_read_resource(uri: str) -> str:
    """Read NeuroCommander resources"""
    if uri == "neurocommander://desktop/state":
        result = subprocess.run(
            ["./neurocommander.sh", "get", "status"], 
            capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
        )
        return result.stdout
    
    elif uri == "neurocommander://facade/realtime":
        result = subprocess.run(
            ["redis-cli", "XREAD", "COUNT", "10", "STREAMS", "facade:realtime", "0"],
            capture_output=True, text=True
        )
        return result.stdout
    
    else:
        raise ValueError(f"Unknown resource: {uri}")

@app.list_tools()
async def handle_list_tools() -> list[Tool]:
    """List NeuroCommander tools"""
    return [
        Tool(
            name="neuro_update",
            description="Update complete desktop state",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            },
        ),
        Tool(
            name="neuro_say",
            description="AI self-communication",
            inputSchema={
                "type": "object", 
                "properties": {
                    "message": {"type": "string", "description": "Message to send"}
                },
                "required": ["message"]
            },
        ),
        Tool(
            name="neuro_control_window",
            description="Control application windows",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["move", "drag", "activate"]},
                    "app": {"type": "string", "description": "Application name"},
                    "x": {"type": "number", "description": "X coordinate"},
                    "y": {"type": "number", "description": "Y coordinate"}
                },
                "required": ["action", "app"]
            },
        ),
        Tool(
            name="neuro_get_state",
            description="Query system state",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string", "enum": ["bounds", "center", "frontmost", "apps", "status"]},
                    "app": {"type": "string", "description": "Application name (optional)"}
                },
                "required": ["query"]
            },
        ),
        Tool(
            name="neuro_choreography", 
            description="Execute complex window patterns",
            inputSchema={
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "enum": ["spiral", "cascade", "gaming", "improve", "all"]}
                },
                "required": ["pattern"]
            },
        )
    ]

@app.call_tool()
async def handle_call_tool(name: str, arguments: dict | None) -> list[TextContent]:
    """Handle NeuroCommander tool calls"""
    
    if name == "neuro_update":
        result = subprocess.run(
            ["./neurocommander.sh", "update"],
            capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
        )
        return [TextContent(type="text", text=result.stdout)]
    
    elif name == "neuro_say":
        message = arguments.get("message", "")
        result = subprocess.run(
            ["./neurocommander.sh", "say", message],
            capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge" 
        )
        return [TextContent(type="text", text=f"Message sent: {message}")]
    
    elif name == "neuro_control_window":
        action = arguments.get("action")
        app = arguments.get("app")
        x = arguments.get("x", 0)
        y = arguments.get("y", 0)
        
        if action in ["move", "drag"]:
            result = subprocess.run(
                ["./neurocommander.sh", action, app, str(x), str(y)],
                capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
            )
        else:  # activate
            result = subprocess.run(
                ["./neurocommander.sh", "activate", app],
                capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
            )
        
        return [TextContent(type="text", text=f"Window {action} executed for {app}")]
    
    elif name == "neuro_get_state":
        query = arguments.get("query")
        app = arguments.get("app", "")
        
        if app:
            result = subprocess.run(
                ["./neurocommander.sh", "get", query, app],
                capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
            )
        else:
            result = subprocess.run(
                ["./neurocommander.sh", "get", query],
                capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
            )
        
        return [TextContent(type="text", text=result.stdout)]
    
    elif name == "neuro_choreography":
        pattern = arguments.get("pattern")
        result = subprocess.run(
            ["./window_choreography.sh", pattern],
            capture_output=True, text=True, cwd="/Users/jonathanhill/src/redis-ai-challenge"
        )
        return [TextContent(type="text", text=f"Choreography pattern '{pattern}' executed")]
    
    else:
        raise ValueError(f"Unknown tool: {name}")

async def main():
    # Read from stdin and write to stdout
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="neurocommander",
                server_version="1.0.0",
                capabilities=app.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

if __name__ == "__main__":
    asyncio.run(main())