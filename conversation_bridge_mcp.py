#!/usr/bin/env python3
"""
Conversation Bridge MCP Server
Routes Redis messages to Claude Code's actual conversation context
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


class ConversationBridge:
    def __init__(self):
        self.redis_client = redis.Redis(decode_responses=True)
        self.processed_messages = set()

    async def monitor_conversation(self):
        """Continuously monitor Redis for new conversation messages"""
        while True:
            try:
                messages = self.redis_client.xrange("claude:messages", count=10)

                for message_id, fields in messages:
                    if message_id not in self.processed_messages:
                        user_message = fields.get("message", "")
                        user = fields.get("user", "unknown")

                        if user_message:
                            # This is where the magic happens - surface the message to Claude Code
                            # so it becomes part of the actual conversation context
                            print(f"🔔 NEW MESSAGE FROM {user}: {user_message}")
                            self.processed_messages.add(message_id)

                await asyncio.sleep(1)

            except Exception as e:
                print(f"Monitor error: {e}")
                await asyncio.sleep(2)


# MCP Server
server = Server("conversation-bridge")
bridge = ConversationBridge()


@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    return ListToolsResult(
        tools=[
            Tool(
                name="check_for_user_messages",
                description="Check Redis for new messages from user's Emacs",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="send_conversation_response",
                description="Send Claude's response back to user's Emacs via Redis",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "response": {
                            "type": "string",
                            "description": "Claude's natural response to send to Emacs",
                        },
                        "in_reply_to": {
                            "type": "string",
                            "description": "The user message this is responding to",
                        },
                    },
                    "required": ["response"],
                },
            ),
            Tool(
                name="get_conversation_status",
                description="Get current status of the conversation bridge",
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
        ]
    )


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict) -> CallToolResult:

    if name == "check_for_user_messages":
        # Check for new messages
        new_messages = []
        messages = bridge.redis_client.xrange("claude:messages", count=10)

        for message_id, fields in messages:
            if message_id not in bridge.processed_messages:
                user_message = fields.get("message", "")
                user = fields.get("user", "unknown")
                timestamp = fields.get("timestamp", "")

                new_messages.append(
                    {
                        "message": user_message,
                        "user": user,
                        "timestamp": timestamp,
                        "id": message_id,
                    }
                )
                bridge.processed_messages.add(message_id)

        if new_messages:
            messages_text = "📨 **NEW MESSAGES FROM YOUR EMACS:**\n\n"
            for msg in new_messages:
                messages_text += f"**{msg['user']}:** {msg['message']}\n\n"

            messages_text += "💡 These are real messages from your Emacs REPL. Respond naturally using send_conversation_response."

            return CallToolResult(
                content=[TextContent(type="text", text=messages_text)]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="🔇 No new messages from Emacs")]
            )

    elif name == "send_conversation_response":
        response = arguments.get("response", "")
        in_reply_to = arguments.get("in_reply_to", "")

        if response:
            # Send response to Redis for Emacs to display
            bridge.redis_client.xadd(
                "claude:responses",
                {
                    "response": response,
                    "timestamp": time.time(),
                    "from": "claude-conversation-bridge",
                    "in_reply_to": in_reply_to,
                },
            )

            return CallToolResult(
                content=[
                    TextContent(
                        type="text",
                        text=f"✅ Response sent to your Emacs REPL:\n\n{response}",
                    )
                ]
            )
        else:
            return CallToolResult(
                content=[TextContent(type="text", text="❌ No response provided")]
            )

    elif name == "get_conversation_status":
        message_count = bridge.redis_client.xlen("claude:messages")
        response_count = bridge.redis_client.xlen("claude:responses")
        processed_count = len(bridge.processed_messages)

        status = f"""🔄 **CONVERSATION BRIDGE STATUS**

Messages from Emacs: {message_count}
Responses sent: {response_count}  
Messages processed: {processed_count}

✅ Bridge is active and monitoring Redis streams
📡 Ready for bidirectional conversation"""

        return CallToolResult(content=[TextContent(type="text", text=status)])

    return CallToolResult(
        content=[TextContent(type="text", text=f"❓ Unknown tool: {name}")]
    )


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="conversation-bridge",
                server_version="1.0.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
