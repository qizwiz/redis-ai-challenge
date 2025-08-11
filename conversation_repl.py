#!/usr/bin/env python3
"""
Conversation REPL - Direct bidirectional conversation through Redis
Creates MCP server for Claude to participate in Emacs conversation
"""

import asyncio
import redis
import time
import signal
import sys
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


class ConversationREPL:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.processed_messages = set()

    def get_new_messages(self):
        """Get new messages from user's Emacs"""
        messages = self.redis_client.xrange("claude:messages", count=10)
        new_messages = []

        for message_id, fields in messages:
            if message_id not in self.processed_messages:
                new_messages.append(
                    {
                        "id": message_id,
                        "message": fields.get("message", ""),
                        "user": fields.get("user", "unknown"),
                        "timestamp": fields.get("timestamp", ""),
                    }
                )
                self.processed_messages.add(message_id)

        return new_messages

    def send_response(self, response_text, in_reply_to=""):
        """Send response back to user's Emacs"""
        self.redis_client.xadd(
            "claude:responses",
            {
                "response": response_text,
                "timestamp": time.time(),
                "from": "conversation-repl-mcp",
                "in_reply_to": in_reply_to,
            },
        )


# MCP Server
server = Server("conversation-repl")
repl = ConversationREPL()


@server.list_tools()
async def list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="check_messages",
                description="Check for new messages from user's Emacs REPL",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="respond",
                description="Send response back to user's Emacs REPL",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "Response message to send to user",
                        },
                        "in_reply_to": {
                            "type": "string",
                            "description": "Message this is replying to",
                        },
                    },
                    "required": ["message"],
                },
            ),
            Tool(
                name="conversation_status",
                description="Get current conversation status and stream info",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]
    )


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "check_messages":
        new_messages = repl.get_new_messages()

        if new_messages:
            result = "📨 **NEW MESSAGES FROM EMACS:**\n\n"
            for msg in new_messages:
                result += f"**{msg['user']}:** {msg['message']}\n\n"
            result += "Use the 'respond' tool to reply."
        else:
            result = "🔇 No new messages from Emacs REPL"

        return CallToolResult(content=[TextContent(type="text", text=result)])

    elif name == "respond":
        message = arguments.get("message", "")
        in_reply_to = arguments.get("in_reply_to", "")

        if message:
            repl.send_response(message, in_reply_to)
            return CallToolResult(
                content=[
                    TextContent(
                        type="text", text=f"✅ Response sent to Emacs:\n\n{message}"
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ No message provided")]
            )

    elif name == "conversation_status":
        message_count = repl.redis_client.xlen("claude:messages")
        response_count = repl.redis_client.xlen("claude:responses")

        status = f"""🔄 **CONVERSATION STATUS**
        
Messages from Emacs: {message_count}
Responses sent: {response_count}
Processed messages: {len(repl.processed_messages)}

✅ Ready for bidirectional conversation"""

        return CallToolResult(content=[TextContent(type="text", text=status)])

    return CallToolResult(
        content=[TextContent(type="text", text=f"❓ Unknown tool: {name}")]
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream, write_stream, server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
