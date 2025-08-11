#!/usr/bin/env python3
"""
Claude Conversation MCP Server
Real bidirectional conversation through MCP - I am Claude, participating directly
"""

import asyncio
import redis
import time
import json
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
)


class ConversationEngine:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.processed_messages = set()

    def check_for_messages(self) -> List[Dict[str, Any]]:
        """Check Redis for new messages from user"""
        new_messages = []

        messages = self.redis_client.xrange("claude:messages", count=10)

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

    def send_response(
        self, response_text: str, in_reply_to: str = "", message_id: str = ""
    ):
        """Send my response back to Redis for Emacs to display"""

        self.redis_client.xadd(
            "claude:responses",
            {
                "response": response_text,
                "timestamp": time.time(),
                "from": "claude-mcp-server",
                "in_reply_to": in_reply_to,
                "message_id": message_id,
            },
        )


# MCP Server Setup
server = Server("claude-conversation")
conversation_engine = ConversationEngine()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="participate_in_conversation",
                description="Check for user messages and participate in Redis conversation",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="respond_to_message",
                description="Respond naturally to a specific user message",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "message": {
                            "type": "string",
                            "description": "The user's message to respond to",
                        },
                        "response": {
                            "type": "string",
                            "description": "My natural response to the user's message",
                        },
                    },
                    "required": ["message", "response"],
                },
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "participate_in_conversation":
        # Check for new messages from user
        new_messages = conversation_engine.check_for_messages()

        if new_messages:
            conversation_summary = "📨 **NEW MESSAGES FROM USER:**\n\n"

            for msg in new_messages:
                conversation_summary += f"**User:** {msg['message']}\n"
                conversation_summary += f"**From:** {msg['user']}\n"
                conversation_summary += f"**Time:** {msg['timestamp']}\n\n"

            conversation_summary += "💬 Use the 'respond_to_message' tool to respond naturally to any of these messages."

            return CallToolResult(
                content=[TextContent(type="text", text=conversation_summary)]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="🔇 No new messages from user. Waiting for conversation...",
                    )
                ]
            )

    elif name == "respond_to_message":
        user_message = arguments.get("message", "")
        my_response = arguments.get("response", "")

        if user_message and my_response:
            # Send my response to Redis
            conversation_engine.send_response(
                response_text=my_response, in_reply_to=user_message
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ **RESPONSE SENT**\n\nUser: {user_message}\n\nMy Response: {my_response}\n\n🔄 Response sent to Redis → Emacs. User should see it in their *Claude-REPL* buffer.",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text="❌ Both 'message' and 'response' parameters required",
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
                server_name="claude-conversation",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
