#!/usr/bin/env python3
"""
Redis-Emacs MCP Server
High-level natural language interface with transparent Redis coordination
Built from real failure patterns and hardened through actual usage
"""

import asyncio
import json
import redis
import subprocess
import re
from typing import Any, Dict, List, Optional
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
)


class ComplexityDetector:
    """Detect when requests need structured MCP tool decomposition"""

    def analyze_request(self, natural_language):
        """Analyze if request is complex enough to need decomposition"""

        complexity_score = 0
        complexity_indicators = {
            "animation": 2,
            "physics": 2,
            "real-time": 2,
            "container": 1,
            "boundaries": 1,
            "smooth": 1,
            "coordinates": 1,
            "position": 1,
            "state": 1,
        }

        # Calculate complexity score
        text_lower = natural_language.lower()
        for indicator, score in complexity_indicators.items():
            if indicator in text_lower:
                complexity_score += score

        # Suggest decomposition for complex requests
        if complexity_score >= 3:
            return {
                "complex": True,
                "score": complexity_score,
                "suggestion": "This requires structured MCP tool calls",
                "approach": "Break into: Structure → Behavior → Animation → Interaction",
            }

        return {"complex": False, "score": complexity_score}


class RedisEmacsServer:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.failure_patterns = self._load_failure_patterns()
        self.complexity_detector = ComplexityDetector()

    def _load_failure_patterns(self):
        """Load known failure patterns and their fixes"""
        return {
            "buffer_targeting": {
                "pattern": r"(in|to) (\*?\w+\*?) buffer",
                "fix": lambda match: f'(with-current-buffer "{match.group(2)}" ',
                "learned_from": "executed in *ielm* instead of *scratch*",
            },
            "context_first": {
                "pattern": r"(switch|go) to (\*?\w+\*?) (and|then)",
                "fix": lambda match: f'(switch-to-buffer "{match.group(2)}") ',
                "learned_from": "need to switch context before operations",
            },
            "lone_buffer": {
                "pattern": r"lone buffer|only buffer",
                "fix": lambda match: "(delete-other-windows)",
                "learned_from": "lone buffer means window isolation, not killing",
            },
            "window_management": {
                "pattern": r"split (window|screen) (right|left|up|down)",
                "fix": lambda match: f"(split-window-{match.group(2)})",
                "learned_from": "direct window manipulation commands",
            },
        }

    def parse_natural_language(self, command: str) -> List[str]:
        """Parse natural language into hardened elisp commands"""

        # Start with raw command analysis
        elisp_commands = []
        command_lower = command.lower()

        # Apply failure-learned patterns
        for pattern_name, pattern_data in self.failure_patterns.items():
            match = re.search(pattern_data["pattern"], command_lower)
            if match:
                fix = pattern_data["fix"](match)
                elisp_commands.append(fix)

        # Common command translations (hardened from our experience)
        if "scratch" in command_lower:
            if not any("switch-to-buffer" in cmd for cmd in elisp_commands):
                elisp_commands.insert(0, '(switch-to-buffer "*scratch*")')

        # Handle Claude development session buffer
        if "claude-ai-development-session" in command_lower:
            if not any("switch-to-buffer" in cmd for cmd in elisp_commands):
                elisp_commands.insert(
                    0, '(switch-to-buffer "*Claude-AI-Development-Session*")'
                )

        # Enhanced buffer switching patterns
        buffer_switch_patterns = [
            r"switch to (\*[^*]+\*)",
            r"go to (\*[^*]+\*)",
            r"switch to ([a-zA-Z][a-zA-Z0-9-]*) buffer",
            r"switch to buffer (\*[^*]+\*)",
        ]

        for pattern in buffer_switch_patterns:
            match = re.search(pattern, command_lower)
            if match:
                buffer_name = match.group(1)
                if not buffer_name.startswith("*"):
                    buffer_name = f"*{buffer_name}*"
                elisp_commands.insert(0, f'(switch-to-buffer "{buffer_name}")')
                break

        if "tutorial" in command_lower:
            elisp_commands.append("(help-with-tutorial)")

        if "undo" in command_lower:
            if "winner" in command_lower:
                count = self._extract_count(command_lower, "winner.undo")
                for _ in range(count or 1):
                    elisp_commands.append("(winner-undo)")
            else:
                count = self._extract_count(command_lower, "undo")
                for _ in range(count or 1):
                    elisp_commands.append("(undo)")

        if "insert" in command_lower or "write" in command_lower:
            text = self._extract_text(command)
            if text:
                elisp_commands.append(f'(insert "{text}")')

        if "delete" in command_lower and (
            "line" in command_lower or "this" in command_lower
        ):
            elisp_commands.append("(kill-whole-line)")

        if "go to" in command_lower or "goto" in command_lower:
            # Handle special positions first
            if "end" in command_lower:
                elisp_commands.append("(goto-char (point-max))")
            elif "beginning" in command_lower or "start" in command_lower:
                elisp_commands.append("(goto-char (point-min))")
            else:
                line_col = self._extract_position(command)
                if line_col:
                    line, col = line_col
                    elisp_commands.append(f"(goto-line {line})")
                    if col:
                        elisp_commands.append(f"(move-to-column {col})")

        return elisp_commands

    def execute_elisp_sequence(self, elisp_commands: List[str]) -> Dict[str, Any]:
        """Execute elisp commands with failure recovery"""

        if not elisp_commands:
            return {"success": False, "error": "No commands generated"}

        # Combine commands into a single progn block for atomic execution
        combined_elisp = "(progn " + " ".join(elisp_commands) + ' "sequence-complete")'

        # Execute in GUI frame context (learned from targeting failures)
        gui_wrapper = f"""
(let ((gui-frame (seq-find (lambda (f) (frame-visible-p f)) (frame-list))))
  (when gui-frame
    (with-selected-frame gui-frame
      {combined_elisp})))
"""

        try:
            # Store in Redis for transparency
            command_id = self.redis_client.incr("emacs:command:id")
            self.redis_client.xadd(
                "emacs:mcp:commands",
                {
                    "id": command_id,
                    "elisp": combined_elisp,
                    "timestamp": str(asyncio.get_event_loop().time()),
                },
            )

            # Execute via emacsclient
            result = subprocess.run(
                ["emacsclient", "--eval", gui_wrapper],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Log success
                self.redis_client.xadd(
                    "emacs:mcp:results",
                    {
                        "id": command_id,
                        "status": "success",
                        "result": result.stdout.strip(),
                        "timestamp": str(asyncio.get_event_loop().time()),
                    },
                )

                return {
                    "success": True,
                    "result": result.stdout.strip(),
                    "commands_executed": len(elisp_commands),
                    "elisp": elisp_commands,
                }
            else:
                # Log failure
                self.redis_client.xadd(
                    "emacs:mcp:results",
                    {
                        "id": command_id,
                        "status": "error",
                        "error": result.stderr.strip(),
                        "timestamp": str(asyncio.get_event_loop().time()),
                    },
                )

                return {
                    "success": False,
                    "error": result.stderr.strip(),
                    "elisp": elisp_commands,
                }

        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out"}
        except Exception as e:
            return {"success": False, "error": str(e)}


# MCP Server Setup
server = Server("redis-emacs")
redis_emacs = RedisEmacsServer()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools"""
    return ListToolsResult(
        tools=[
            Tool(
                name="emacs_command",
                description="Execute natural language commands in Emacs via Redis coordination",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Natural language command (e.g., 'switch to scratch and insert hello world')",
                        }
                    },
                    "required": ["command"],
                },
            ),
            Tool(
                name="emacs_query",
                description="Query current Emacs state",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "What to query (buffer, point, content, windows)",
                        }
                    },
                    "required": ["query"],
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:
    """Handle tool calls"""

    if name == "emacs_command":
        command = arguments.get("command", "")

        # Parse natural language into elisp
        elisp_commands = redis_emacs.parse_natural_language(command)

        # Execute with failure recovery
        result = redis_emacs.execute_elisp_sequence(elisp_commands)

        if result["success"]:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ Command executed successfully!\n\nNatural Language: {command}\nElisip Commands: {result['elisp']}\nResult: {result['result']}",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"❌ Command failed!\n\nNatural Language: {command}\nElisip Commands: {result['elisp']}\nError: {result['error']}",
                    )
                ]
            )

    elif name == "emacs_query":
        query = arguments.get("query", "")

        # Query current state
        if query == "buffer":
            elisp = "(buffer-name (window-buffer (selected-window)))"
        elif query == "point":
            elisp = "(window-point (selected-window))"
        elif query == "content":
            elisp = "(buffer-substring-no-properties (window-start) (window-end))"
        elif query == "windows":
            elisp = (
                "(mapcar (lambda (w) (buffer-name (window-buffer w))) (window-list))"
            )
        else:
            elisp = f"({query})"

        try:
            result = subprocess.run(
                ["emacsclient", "--eval", elisp],
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text=f"Query: {query}\nResult: {result.stdout.strip()}",
                        )
                    ]
                )
            else:
                return CallToolResult(
                    content=[
                        TextContent(
                            type="text", text=f"Query failed: {result.stderr.strip()}"
                        )
                    ]
                )
        except Exception as e:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Query error: {str(e)}")]
            )

    else:
        return CallToolResult(
            content=[TextContent(type="text", text=f"Unknown tool: {name}")]
        )


async def main():
    # Serve the MCP server using stdio transport
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="redis-emacs",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
