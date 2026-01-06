#!/usr/bin/env python3
"""
Natural Language Emacs MCP Server
An MCP server that lets Claude talk to Emacs in natural language
"""

import asyncio
import json
import subprocess
from typing import Any
from mcp.server import Server
from mcp.types import Tool, TextContent

app = Server("natural-language-emacs")

def emacs_eval(elisp: str) -> str:
    """Evaluate Elisp code in running Emacs daemon"""
    try:
        result = subprocess.run(
            ['emacsclient', '--eval', elisp],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else f"Error: {result.stderr}"
    except Exception as e:
        return f"Error: {e}"

@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available natural language Emacs tools"""
    return [
        Tool(
            name="emacs_say",
            description="Talk to Emacs in natural language. I will translate your intent to Emacs commands. Examples: 'insert hello world', 'go to line 10', 'save this buffer', 'what's my current position?'",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Natural language command for Emacs"
                    }
                },
                "required": ["command"]
            }
        ),
        Tool(
            name="emacs_do",
            description="Execute specific Emacs actions. More structured than emacs_say.",
            inputSchema={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["insert", "move", "delete", "save", "status", "search"],
                        "description": "Action to perform"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "Action parameters",
                        "properties": {
                            "text": {"type": "string"},
                            "position": {"type": "string"},
                            "line": {"type": "number"}
                        }
                    }
                },
                "required": ["action"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """Handle tool calls"""

    if name == "emacs_say":
        command = arguments["command"]
        command_lower = command.lower()

        # Parse natural language
        if "insert" in command_lower or "type" in command_lower:
            # Extract text to insert
            for trigger in ["insert", "type", "write"]:
                if trigger in command_lower:
                    idx = command_lower.index(trigger) + len(trigger)
                    text = command[idx:].strip(' "\'')
                    result = emacs_eval(f'(insert "{text}")')
                    return [TextContent(type="text", text=f"Inserted: {text}\nResult: {result}")]

        elif "move" in command_lower or "go" in command_lower:
            if "beginning" in command_lower or "start" in command_lower:
                result = emacs_eval('(goto-char (point-min))')
                return [TextContent(type="text", text=f"Moved to beginning. Result: {result}")]
            elif "end" in command_lower:
                result = emacs_eval('(goto-char (point-max))')
                return [TextContent(type="text", text=f"Moved to end. Result: {result}")]
            elif "line" in command_lower:
                # Extract line number
                words = command_lower.split()
                for word in words:
                    if word.isdigit():
                        line = int(word)
                        result = emacs_eval(f'(goto-line {line})')
                        return [TextContent(type="text", text=f"Moved to line {line}. Result: {result}")]

        elif "delete" in command_lower or "kill" in command_lower:
            if "line" in command_lower:
                result = emacs_eval('(kill-line)')
                return [TextContent(type="text", text=f"Deleted line. Result: {result}")]
            elif "word" in command_lower:
                result = emacs_eval('(kill-word 1)')
                return [TextContent(type="text", text=f"Deleted word. Result: {result}")]

        elif "save" in command_lower:
            result = emacs_eval('(save-buffer)')
            return [TextContent(type="text", text=f"Saved buffer. Result: {result}")]

        elif "status" in command_lower or "where" in command_lower or "what" in command_lower:
            buffer = emacs_eval('(buffer-name)')
            point = emacs_eval('(point)')
            line = emacs_eval('(line-number-at-pos)')
            return [TextContent(type="text", text=f"Buffer: {buffer}, Point: {point}, Line: {line}")]

        else:
            return [TextContent(type="text", text=f"I don't understand: {command}")]

    elif name == "emacs_do":
        action = arguments["action"]
        params = arguments.get("parameters", {})

        if action == "insert":
            text = params.get("text", "")
            result = emacs_eval(f'(insert "{text}")')
            return [TextContent(type="text", text=f"Inserted: {text}")]

        elif action == "move":
            position = params.get("position")
            line = params.get("line")

            if position == "beginning":
                emacs_eval('(goto-char (point-min))')
                return [TextContent(type="text", text="Moved to beginning")]
            elif position == "end":
                emacs_eval('(goto-char (point-max))')
                return [TextContent(type="text", text="Moved to end")]
            elif line:
                emacs_eval(f'(goto-line {line})')
                return [TextContent(type="text", text=f"Moved to line {line}")]

        elif action == "status":
            buffer = emacs_eval('(buffer-name)')
            point = emacs_eval('(point)')
            line = emacs_eval('(line-number-at-pos)')
            return [TextContent(type="text", text=f"Buffer: {buffer}, Point: {point}, Line: {line}")]

    return [TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    """Run the MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )

if __name__ == "__main__":
    asyncio.run(main())
