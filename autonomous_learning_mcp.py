#!/usr/bin/env python3
"""
Autonomous Learning MCP Server
System that learns patterns and applies fixes automatically
"""

import asyncio
from mcp.server import InitializationOptions, NotificationOptions, Server
from mcp import stdio_server
from mcp.types import (
    CallToolRequest,
    CallToolResult,
    ListToolsRequest,
    ListToolsResult,
    Tool,
    TextContent,
)

from autonomous_learning_system import AutonomousLearningSystem

server = Server("autonomous-learning")
learning_system = AutonomousLearningSystem()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="run_learning_cycle",
                description="Run autonomous learning cycle to detect patterns and synthesize fixes",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="apply_learned_patterns",
                description="Apply learned patterns to enhance a command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "Command to enhance with learned patterns",
                        }
                    },
                    "required": ["command"],
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "run_learning_cycle":
        patterns = learning_system.autonomous_learning_cycle()

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"""🤖 **AUTONOMOUS LEARNING CYCLE COMPLETE**

✅ Analyzed system behavior patterns
✅ Synthesized {len(patterns)} learned fixes
✅ Stored patterns in Redis for system-wide access

**Patterns Learned:**
{chr(10).join([f"• {p.trigger_condition} → {len(p.learned_fix)} fixes (confidence: {p.confidence:.2f})" for p in patterns])}

🧠 System intelligence upgraded!""",
                )
            ]
        )

    elif name == "apply_learned_patterns":
        command = arguments.get("command", "")
        enhanced = learning_system.apply_learned_patterns(command)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"""🔧 **PATTERN APPLICATION**

**Original**: {command}
**Enhanced**: {enhanced}

{'✅ Patterns applied!' if enhanced != command else '❌ No patterns matched'}""",
                )
            ]
        )

    return CallToolResult(
        content=[TextContent(type="text", text=f"❓ Unknown tool: {name}")]
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="autonomous-learning",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
