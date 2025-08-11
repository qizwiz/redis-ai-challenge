#!/usr/bin/env python3
"""
MCP AI Assistant Server - Expose learning AI through Model Context Protocol
"""

import asyncio
import json
import subprocess
import sys  # Import sys for stderr
from typing import Any, Dict, List, Optional

print("MCP AI Assistant: Before mcp.server import.", file=sys.stderr)
from mcp.server import Server, NotificationOptions
from mcp.server.models import InitializationOptions
import mcp.server.stdio
import mcp.types as types

print("MCP AI Assistant: Before genuine_ai_learning import.", file=sys.stderr)
from genuine_ai_learning import RealLearner

print("MCP AI Assistant: All imports done.", file=sys.stderr)


class MCPAIAssistant:
    """MCP server wrapper for the learning AI assistant"""

    def __init__(self):
        print("MCPAIAssistant: __init__ started.", file=sys.stderr)
        try:
            self.learner = RealLearner()
            print("MCPAIAssistant: RealLearner initialized.", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing RealLearner: {e}", file=sys.stderr)
            raise  # Re-raise to prevent silent exit
        self.emacs_available = False
        self._check_emacs_connection()
        print("MCPAIAssistant: __init__ finished.", file=sys.stderr)

    def _check_emacs_connection(self):
        """Checks if Emacs server is running and updates emacs_available status."""
        try:
            # emacsclient returns 0 if server is running, non-zero otherwise
            result = subprocess.run(
                ["emacsclient", "--eval", "(server-running-p)"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            self.emacs_available = result.returncode == 0
            if not self.emacs_available:
                print("Emacs server not running or not accessible.", file=sys.stderr)
        except Exception as e:
            print(f"Error checking Emacs connection: {e}", file=sys.stderr)
            self.emacs_available = False


print("MCP AI Assistant: Before Server instantiation.", file=sys.stderr)
# Create the MCP server
server = Server("ai-assistant")
print("MCP AI Assistant: Server instantiated.", file=sys.stderr)
ai_assistant = MCPAIAssistant()
print("MCP AI Assistant: MCPAIAssistant instantiated.", file=sys.stderr)


@server.list_tools()
async def handle_list_tools() -> List[types.Tool]:
    """List available AI assistant tools"""
    return [
        types.Tool(
            name="execute_command",
            description="Execute a natural language command using the learning AI assistant",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Natural language command to execute (e.g., 'move cursor forward', 'save file', 'show git status')",
                    },
                    "learn": {
                        "type": "boolean",
                        "description": "Whether the AI should learn from this interaction (default: true)",
                        "default": True,
                    },
                },
                "required": ["command"],
            },
        ),
        types.Tool(
            name="get_ai_knowledge",
            description="Get the AI's current knowledge base and learning statistics",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
        types.Tool(
            name="teach_ai",
            description="Explicitly teach the AI a new command mapping",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Natural language command",
                    },
                    "key_binding": {
                        "type": "string",
                        "description": "Emacs key binding or action (e.g., 'C-f', 'M-x magit-status')",
                    },
                    "intent": {
                        "type": "string",
                        "description": "Command intent category",
                        "enum": [
                            "navigation",
                            "editing",
                            "file_ops",
                            "git_ops",
                            "debugging",
                        ],
                    },
                },
                "required": ["command", "key_binding", "intent"],
            },
        ),
        types.Tool(
            name="check_emacs_status",
            description="Check if Emacs is available for real command execution",
            inputSchema={
                "type": "object",
                "properties": {},
                "additionalProperties": False,
            },
        ),
    ]


@server.call_tool()
async def handle_call_tool(
    name: str, arguments: Dict[str, Any]
) -> List[types.TextContent]:
    """Handle tool calls to the AI assistant"""

    if name == "execute_command":
        command = arguments["command"]
        learn = arguments.get("learn", True)

        # Use the learning AI to attempt the command
        result = ai_assistant.learner.attempt_command(command)

        response = {
            "command": command,
            "analysis": {
                "intent": result["analysis"]["intent"],
                "confidence": result["adjusted_confidence"],
                "method": result["analysis"]["method"],
            },
            "execution": result["execution"],
            "learning": (
                result["learning"]
                if learn
                else {"learned": False, "insight": "Learning disabled"}
            ),
            "emacs_available": ai_assistant.emacs_available,
        }

        # Try real execution if possible
        if result["execution"]["outcome"] == "success" and ai_assistant.emacs_available:
            key_binding = result["execution"].get("key_used")
            if key_binding:
                try:
                    # Execute in real Emacs
                    if key_binding.startswith("M-x"):
                        cmd = key_binding.replace("M-x ", "")
                        elisp = f'(call-interactively (intern "{cmd}"))'
                    else:
                        elisp = f'(call-interactively (key-binding "{key_binding}"))'

                    exec_result = subprocess.run(
                        ["emacsclient", "--eval", elisp],
                        capture_output=True,
                        text=True,
                        timeout=10,
                    )

                    response["real_execution"] = {
                        "attempted": True,
                        "success": exec_result.returncode == 0,
                        "output": (
                            exec_result.stdout
                            if exec_result.returncode == 0
                            else exec_result.stderr
                        ),
                    }
                except Exception as e:
                    response["real_execution"] = {
                        "attempted": True,
                        "success": False,
                        "error": str(e),
                    }

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    elif name == "get_ai_knowledge":
        knowledge_summary = {
            "patterns_learned": len(ai_assistant.learner.knowledge),
            "knowledge_base": ai_assistant.learner.knowledge,
            "confidence_adjustments": ai_assistant.learner.confidence_adjustments,
            "total_experiences": ai_assistant.learner.memory.redis_client.xlen(
                "ai_experiences"
            ),
            "session_id": ai_assistant.learner.memory.session_id,
        }

        return [
            types.TextContent(type="text", text=json.dumps(knowledge_summary, indent=2))
        ]

    elif name == "teach_ai":
        command = arguments["command"]
        key_binding = arguments["key_binding"]
        intent = arguments["intent"]

        # Manually add to knowledge base
        pattern_key = f"{intent}:{command.lower()}"
        ai_assistant.learner.knowledge[pattern_key] = {
            "key_binding": key_binding,
            "action": f"execute_{intent}",
            "times_successful": 1,
            "manually_taught": True,
        }

        # Record the teaching experience
        teaching_result = {
            "outcome": "success",
            "key_used": key_binding,
            "learned": True,
            "manually_taught": True,
        }

        ai_assistant.learner.memory.record_experience(
            command, {"intent": intent, "method": "manual_teaching"}, teaching_result
        )

        response = {
            "taught": True,
            "pattern": pattern_key,
            "mapping": f"{command} → {key_binding}",
            "total_patterns": len(ai_assistant.learner.knowledge),
        }

        return [types.TextContent(type="text", text=json.dumps(response, indent=2))]

    elif name == "check_emacs_status":
        ai_assistant._check_emacs_connection()

        status = {
            "emacs_available": ai_assistant.emacs_available,
            "can_execute_commands": ai_assistant.emacs_available,
            "instructions": {
                "if_not_available": [
                    "1. Start Emacs: emacs &",
                    "2. Enable server: M-x server-start",
                    "3. Try commands again",
                ]
            },
        }

        return [types.TextContent(type="text", text=json.dumps(status, indent=2))]

    else:
        raise ValueError(f"Unknown tool: {name}")


async def main():
    """Run the MCP AI assistant server"""
    print("MCP AI Assistant: main() started.", file=sys.stderr)
    # Run the server using stdin/stdout streams
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        print("MCP AI Assistant: stdio_server context entered.", file=sys.stderr)
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="ai-assistant",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )
        print("MCP AI Assistant: server.run() finished.", file=sys.stderr)


if __name__ == "__main__":
    print("MCP AI Assistant: Script about to run main().", file=sys.stderr)
    asyncio.run(main())
    print("MCP AI Assistant: Script finished.", file=sys.stderr)
