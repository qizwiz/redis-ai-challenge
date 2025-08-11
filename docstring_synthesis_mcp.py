#!/usr/bin/env python3
"""
Docstring Synthesis MCP Server
Background learning from Emacs docstrings for semantic intelligence
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

from docstring_synthesis_engine import DocstringSynthesisEngine


class DocstringSynthesisMCP:
    def __init__(self):
        self.engine = DocstringSynthesisEngine()


server = Server("docstring-synthesis")
synthesis_mcp = DocstringSynthesisMCP()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="harvest_docstrings",
                description="Harvest and learn from Emacs docstrings to build semantic mappings",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="lookup_utterance",
                description="Fast lookup: natural language → canonical Emacs command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "utterance": {
                            "type": "string",
                            "description": "Natural language utterance to look up",
                        }
                    },
                    "required": ["utterance"],
                },
            ),
            Tool(
                name="predict_next_actions",
                description="Predict likely next actions after a command",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "current_command": {
                            "type": "string",
                            "description": "Current command to predict from",
                        }
                    },
                    "required": ["current_command"],
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "harvest_docstrings":
        # Build semantic mappings from docstrings
        mappings = synthesis_mcp.engine.build_semantic_mappings()

        # Store in Redis
        synthesis_mcp.engine.store_mappings_in_redis(mappings)

        return CallToolResult(
            content=[
                TextContent(
                    type="text",
                    text=f"""🧠 **DOCSTRING SYNTHESIS COMPLETE**

✅ Harvested {len(mappings)} Emacs functions
✅ Generated semantic mappings with utterance variations  
✅ Stored in Redis for zero-delay lookup

**Sample Mappings:**
{chr(10).join([f"• {m.canonical_command}: {m.synthesized_utterances[:2]}..." for m in mappings[:5]])}

**Coverage:**
- Commands mapped: {len(mappings)}
- Total utterances: {sum(len(m.synthesized_utterances) for m in mappings)}
- Intent categories: {len(set(m.intent_category for m in mappings))}

Ready for instant semantic translation! 🚀""",
                )
            ]
        )

    elif name == "lookup_utterance":
        utterance = arguments.get("utterance", "")
        canonical = synthesis_mcp.engine.lookup_utterance(utterance)

        if canonical:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""🎯 **SEMANTIC LOOKUP SUCCESS**

**Input**: "{utterance}"
**Canonical**: `({canonical})`

✅ Zero-delay semantic translation ready!""",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""❓ **NO MAPPING FOUND**

**Input**: "{utterance}"
**Result**: No semantic mapping found

💡 This utterance could be added to the learning corpus.""",
                    )
                ]
            )

    elif name == "predict_next_actions":
        current_command = arguments.get("current_command", "")
        predictions = synthesis_mcp.engine.predict_next_actions(current_command)

        if predictions:
            pred_text = "\n".join(
                [f"• {cmd}: {score:.1%} likelihood" for cmd, score in predictions[:5]]
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""🔮 **NEXT ACTION PREDICTIONS**

**After**: `({current_command})`

**Likely Next Actions:**
{pred_text}

🧠 Based on semantic relationships from docstrings""",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"""❓ **NO PREDICTIONS AVAILABLE**

**Command**: `({current_command})`

No semantic relationships found in docstring corpus.""",
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
                server_name="docstring-synthesis",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
